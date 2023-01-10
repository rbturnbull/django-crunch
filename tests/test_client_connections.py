import os
import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from rest_framework import status as drf_status
from rest_framework.test import APITestCase
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
