from datetime import datetime
import os, re
import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from rest_framework import status as drf_status
from rest_framework.test import APIClient
from crunch.client import connections
from crunch.django.app.enums import Stage, State
from crunch.django.app import models


class MockResponse():
    def __init__(self, data=None, status_code=200, reason=""):
        self.data = data
        self.status_code = status_code
        self.reason = reason

    def json(self):
        return self.data


@patch('requests.get', lambda *args, **kwargs: MockResponse(data={"detail": "Not found"}))
def test_get_json_response_error():
    connection = connections.Connection(base_url="http://www.example.com", token="token")

    with pytest.raises(connections.CrunchAPIException, match=r"Error getting JSON response from URL 'http://www.example.com/test':"):
        connection.get_json_response("test")


@patch('requests.get', lambda *args, **kwargs: MockResponse(data={"id": "1", "name":"Test Project"}))
def test_get_json_response():
    connection = connections.Connection(base_url="http://www.example.com", token="token")
    result = connection.get_json_response("test")
    assert len(result.keys()) == 2
    assert result['id'] == "1"
    assert result['name'] == "Test Project"


@patch('requests.post', lambda *args, **kwargs: MockResponse(status_code=200))
def test_post():
    connection = connections.Connection(base_url="http://www.example.com", token="token")
    result = connection.post("test")
    assert result.status_code == 200


@patch('requests.post', lambda *args, **kwargs: MockResponse(status_code=200))
def test_post():
    connection = connections.Connection(base_url="http://www.example.com", token="token")
    result = connection.post("test")
    assert result.status_code == 200


@patch('requests.post', lambda *args, **kwargs: MockResponse(status_code=403, reason="Forbidden"))
def test_post_forbidden_verbose(capsys):
    connection = connections.Connection(base_url="http://www.example.com", token="token", verbose=True)
    result = connection.post("test")
    assert result.status_code == 403
    captured = capsys.readouterr()
    assert "Response 403: Forbidden" in captured.out
    assert "Failed posting to http://www.example.com/test" in captured.out


@patch('requests.post', lambda *args, **kwargs: MockResponse(status_code=200))
def test_send_status_sucess():
    connection = connections.Connection(base_url="http://www.example.com", token="token")
    result = connection.send_status("dataset_id", Stage.UPLOAD, State.SUCCESS)
    assert result.status_code == 200


@patch('requests.post', lambda *args, **kwargs: MockResponse(status_code=403, reason="Forbidden"))
def test_send_status_forbidden():
    connection = connections.Connection(base_url="http://www.example.com", token="token")
    with pytest.raises(connections.CrunchAPIException, match=r"Failed sending status\.\n403: Forbidden"):
        connection.send_status("dataset_id", Stage.UPLOAD, State.SUCCESS)


def test_connection_no_url():
    with pytest.raises(connections.CrunchAPIException, match=r"Please provide a base URL"):
        connections.Connection()


def test_connection_no_token():
    with pytest.raises(connections.CrunchAPIException, match=r"Please provide an authentication token"):
        connections.Connection(base_url="http://www.example.com")


def test_connection_url_env():
    os.environ["CRUNCH_URL"] = "http://www.example.com"
    connection = connections.Connection(token="token")
    assert connection.base_url == "http://www.example.com"


def test_connection_token_env():
    os.environ["CRUNCH_TOKEN"] = "token"
    connection = connections.Connection(base_url="http://www.example.com")
    assert connection.token == "token"


def test_connection_absolute_url():
    os.environ["CRUNCH_TOKEN"] = "token"
    assert connections.Connection(base_url="http://www.example.com").absolute_url("data") == "http://www.example.com/data"
    assert connections.Connection(base_url="http://www.example.com/").absolute_url("data") == "http://www.example.com/data"
    assert connections.Connection(base_url="http://www.example.com/").absolute_url("/data") == "http://www.example.com/data"


class MockConnection(connections.Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ContentType.objects.clear_cache()
        self.client = APIClient()
        User = get_user_model()
        self.username = "username"
        self.password = "password-for-unit-testing"
        self.user = User.objects.create_superuser(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)

    def post(self, relative_url, **kwargs):
        if not relative_url.startswith("/"):
            relative_url = f"/{relative_url}"
        return self.client.post(relative_url, kwargs)        


@pytest.mark.django_db
def test_connection_add_project():
    connection = MockConnection(base_url="http://www.example.com/", token="token", verbose=True)
    response = connection.add_project("project", "description", "details")
    assert response.status_code == drf_status.HTTP_201_CREATED

    project = models.Project.objects.get(name="project")
    assert project.description == "description"
    assert project.details == "details"


@pytest.mark.django_db
def test_connection_add_dataset():
    connection = MockConnection(base_url="http://www.example.com/", token="token", verbose=True)
    project = models.Project.objects.create(name="Test Project")    
    response = connection.add_dataset(project.slug, "dataset 2", "description", "details")
    assert response.status_code == drf_status.HTTP_201_CREATED

    dataset = models.Dataset.objects.get(name="dataset 2")
    assert dataset.parent == project
    assert dataset.description == "description"
    assert dataset.details == "details"


@pytest.mark.django_db
def test_connection_add_item():
    connection = MockConnection(base_url="http://www.example.com/", token="token", verbose=True)
    project = models.Project.objects.create(name="Test Project")    
    response = connection.add_item(project.slug, "item", "description", "details")
    assert response.status_code == drf_status.HTTP_201_CREATED

    item = models.Item.objects.get(name="item")
    assert item.parent == project
    assert item.description == "description"
    assert item.details == "details"


@pytest.mark.django_db
def test_connection_add_char_attribute(capsys):
    connection = MockConnection(base_url="http://www.example.com/", token="token", verbose=True)
    project = models.Project.objects.create(name="Test Project")    
    response = connection.add_char_attribute(project.slug, "key1", "value1")
    assert response.status_code == drf_status.HTTP_201_CREATED

    project = models.Project.objects.get(name="Test Project")
    assert project.attributes.count() == 1
    attribute = project.attributes.first()
    assert isinstance(attribute, models.CharAttribute)
    assert attribute.key == "key1"
    assert attribute.value == "value1"

    captured = capsys.readouterr()
    assert "Adding attribute 'key1'->'value1' to item 'test-project' on the hosted site http://www.example.com/" in captured.out.replace("\n", "")


def assert_single_attribute(cls, key, value):
    assert cls.objects.count() == 1
    attribute = cls.objects.first()
    assert attribute.key == key
    assert attribute.value == value


@pytest.mark.django_db
def test_connection_add_attributes():
    connection = MockConnection(base_url="http://www.example.com/", token="token")
    project = models.Project.objects.create(name="Test Project")   
    now = timezone.now()
    connection.add_attributes(
        project.slug,
        url_attribute="http://www.example.com",
        char_attribute="Char info",
        float_attribute=0.5,
        bool_attribute=True,
        int_attribute=42,
        datetime_attribute=now,
        date_attribute=datetime.date(now),
    )
    
    project = models.Project.objects.get(name="Test Project")
    assert_single_attribute(models.CharAttribute, key="char_attribute", value="Char info")
    assert_single_attribute(models.FloatAttribute, key="float_attribute", value=0.5)
    assert_single_attribute(models.BooleanAttribute, key="bool_attribute", value=True)
    assert_single_attribute(models.IntegerAttribute, key="int_attribute", value=42)
    assert_single_attribute(models.DateTimeAttribute, key="datetime_attribute", value=now)
    assert_single_attribute(models.DateAttribute, key="date_attribute", value=datetime.date(now))
    assert_single_attribute(models.URLAttribute, key="url_attribute", value="http://www.example.com")

    assert project.attributes.count() == 7
    

@pytest.mark.django_db
def test_connection_add_url_attribute(capsys):
    connection = MockConnection(base_url="http://www.example.com/", token="token", verbose=True)
    project = models.Project.objects.create(name="Test Project")    
    response = connection.add_url_attribute(project.slug, "key1", "http://www.example.com")
    assert response.status_code == drf_status.HTTP_201_CREATED

    project = models.Project.objects.get(name="Test Project")
    assert project.attributes.count() == 1
    attribute = project.attributes.first()
    assert isinstance(attribute, models.URLAttribute)
    assert attribute.key == "key1"
    assert attribute.value == "http://www.example.com"

    captured = capsys.readouterr()
    assert "Adding attribute 'key1'->'http://www.example.com' to item 'test-project' on the hosted site http://www.example.com/" in captured.out.replace("\n", "")    


@pytest.mark.django_db
def test_connection_add_attributes_unknown_type():
    connection = MockConnection(base_url="http://www.example.com/", token="token")
    project = models.Project.objects.create(name="Test Project")  
    class UnknownObject():
        def __str__(self):
            return "unknown object" 

    with pytest.raises(connections.CrunchAPIException, match=re.escape("Cannot infer type of value 'unknown object' (UnknownObject). (The key was 'object_attribute')")):
        connection.add_attributes(
            project.slug,
            url_attribute="http://www.example.com",
            char_attribute="Char info",
            object_attribute=UnknownObject(),
        )

@pytest.mark.django_db
def test_connection_add_lat_long_attribute(capsys):
    connection = MockConnection(base_url="http://www.example.com/", token="token", verbose=True)
    project = models.Project.objects.create(name="Test Project")    
    response = connection.add_lat_long_attribute(project.slug, "key1", latitude=-20, longitude=40)
    assert response.status_code == drf_status.HTTP_201_CREATED

    project = models.Project.objects.get(name="Test Project")
    assert project.attributes.count() == 1
    attribute = project.attributes.first()
    assert isinstance(attribute, models.LatLongAttribute)
    assert attribute.key == "key1"
    assert attribute.latitude == -20
    assert attribute.longitude == 40

    captured = capsys.readouterr()
    assert "Adding attribute 'key1'->'-20,40' to item 'test-project' on the hosted site http://www.example.com/" in captured.out.replace("\n", "")    

@pytest.mark.django_db
def test_connection_add_filesize_attribute():
    connection = MockConnection(base_url="http://www.example.com/", token="token")
    project = models.Project.objects.create(name="Test Project")    
    response = connection.add_filesize_attribute(project.slug, "key1", value=1_000_000)
    assert response.status_code == drf_status.HTTP_201_CREATED

    project = models.Project.objects.get(name="Test Project")
    assert project.attributes.count() == 1
    attribute = project.attributes.first()
    assert isinstance(attribute, models.FilesizeAttribute)
    assert attribute.key == "key1"
    assert attribute.value == 1_000_000
