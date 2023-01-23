import pytest
from datetime import datetime
import pytz
from typer.testing import CliRunner
from django.test import TestCase
from crunch.client.main import app
from unittest.mock import patch
from crunch.django.app import models
from django.contrib.contenttypes.models import ContentType

from django.core.files.storage import FileSystemStorage

from crunch.client.run import Run
from .test_client_connections import MockConnection, MockResponse
from .test_storages import TEST_DIR

runner = CliRunner()

EXAMPLE_URL =  "http://www.example.com"

class ClientMainTestCase(TestCase):
    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Usage: " in result.stdout

    def test_diagnostics(self):
        result = runner.invoke(app, ["diagnostics"])
        assert result.exit_code == 0
        assert "agent_user" in result.stdout
        assert "version" in result.stdout


def get_mock_connection(url, token, **kwargs):
    assert url == EXAMPLE_URL
    assert token == "token"
    return MockConnection(base_url=url, token=token)


@pytest.mark.django_db
@patch('crunch.client.main.connections.Connection', get_mock_connection )
def test_add_project_command():
    result = runner.invoke(app, [
        "add-project", "project", 
        "--description", "description", 
        "--details", "details", 
        "--url", EXAMPLE_URL, 
        "--token", "token"
    ])
    assert result.exit_code == 0

    assert models.Project.objects.count() == 1
    project = models.Project.objects.get(name="project")
    assert project.description == "description"
    assert project.details == "details"


@pytest.mark.django_db
@patch('crunch.client.main.connections.Connection', get_mock_connection )
def test_add_dataset_command():
    project = models.Project.objects.create(name="Test Project")    

    result = runner.invoke(app, [
        "add-dataset", project.slug, "Dataset", 
        "--description", "description", 
        "--details", "details", 
        "--url", EXAMPLE_URL, 
        "--token", "token"
    ])
    assert result.exit_code == 0

    assert models.Dataset.objects.count() == 1
    dataset = models.Dataset.objects.get(name="Dataset")
    assert dataset.description == "description"
    assert dataset.details == "details"


@pytest.mark.django_db
@patch('crunch.client.main.connections.Connection', get_mock_connection )
def test_add_item_command():
    project = models.Project.objects.create(name="Test Project")    

    result = runner.invoke(app, [
        "add-item", project.slug, "Item", 
        "--description", "description", 
        "--details", "details", 
        "--url", EXAMPLE_URL, 
        "--token", "token"
    ])
    assert result.exit_code == 0

    assert models.Item.objects.count() == 2
    item = models.Item.objects.get(name="Item")
    assert item.description == "description"
    assert item.details == "details"    


@patch('crunch.client.main.connections.Connection', get_mock_connection )
def assert_add_attribute(command, key, value, cls, value_str=None):
    value_str = value_str or str(value)
    project = models.Project.objects.create(name="Test Project")    

    result = runner.invoke(app, [
        command, project.slug, key, value_str, 
        "--url", EXAMPLE_URL, 
        "--token", "token"
    ])
    assert result.exit_code == 0

    assert cls.objects.count() == 1
    attribute = cls.objects.first()
    assert getattr(attribute, "key") == key
    assert getattr(attribute, "value") == value


@pytest.mark.django_db
def test_add_char_attribute():
    assert_add_attribute("add-char-attribute", "key", "value", models.CharAttribute)


@pytest.mark.django_db
def test_add_float_attribute():
    assert_add_attribute("add-float-attribute", "key", 3.14, models.FloatAttribute)


@pytest.mark.django_db
def test_add_datetime_attribute():
    value = datetime(2022, 1, 1, 14, tzinfo=pytz.utc)
    assert_add_attribute("add-datetime-attribute", "key", value, models.DateTimeAttribute, value_str="'2022-01-01 14:00'")


@pytest.mark.django_db
def test_add_date_attribute():
    value = datetime(2022, 1, 1, 14, tzinfo=pytz.utc).date()
    assert_add_attribute("add-date-attribute", "key", value, models.DateAttribute, value_str="2022-01-01")


@pytest.mark.django_db
def test_add_integer_attribute():
    assert_add_attribute("add-integer-attribute", "key", 42, models.IntegerAttribute)


@pytest.mark.django_db
def test_add_filesize_attribute():
    assert_add_attribute("add-filesize-attribute", "key", 1024, models.FilesizeAttribute)


@pytest.mark.django_db
def test_add_boolean_attribute():
    assert_add_attribute("add-boolean-attribute", "key", True, models.BooleanAttribute, value_str="True")


@pytest.mark.django_db
def test_add_url_attribute():
    assert_add_attribute("add-url-attribute", "key", EXAMPLE_URL, models.URLAttribute)


@pytest.mark.django_db
@patch('crunch.client.main.connections.Connection', get_mock_connection )
def test_add_lat_long_attribute():
    cls = models.LatLongAttribute
    key = "key"

    project = models.Project.objects.create(name="Test Project")    

    result = runner.invoke(app, [
        "add-lat-long-attribute", project.slug, "key",
        "--url", EXAMPLE_URL, 
        "--token", "token",
        "--",         # needed because of negative number (https://github.com/pallets/click/issues/555)
        "-20", "40", 
    ])
    assert result.exit_code == 0
    
    assert cls.objects.count() == 1
    attribute = cls.objects.first()
    assert getattr(attribute, "key") == key
    assert getattr(attribute, "latitude") == -20
    assert getattr(attribute, "longitude") == 40


@pytest.mark.django_db
@patch('requests.get', lambda *args, **kwargs: MockResponse(data={"base_file_path": str(TEST_DIR)}))
def test_files_command():
    absolute_path = str(TEST_DIR.absolute())
    storage = FileSystemStorage(location=absolute_path, base_url="http://www.example.com")
    
    with patch('crunch.django.app.storages.default_storage', storage):
        project = models.Project.objects.create(name="Test Project")    
        dataset = models.Dataset.objects.create(name="Test Dataset", parent=project)    
        result = runner.invoke(app, [
            "files", 
            dataset.slug,
            "--storage-settings", str(TEST_DIR/"settings.toml"),
            "--url", EXAMPLE_URL, 
            "--token", "token",
        ])
        assert result.exit_code == 0
        assert "── dummy-files" in result.stdout
        assert "dummy-file2.txt" in result.stdout


dataset_mock_response = MockResponse(data={"id": 2, "slug": "dataset", "parent": "project", "base_file_path": str(TEST_DIR)})
@patch('requests.get', lambda *args, **kwargs: dataset_mock_response)
@patch.object(Run, '__call__', return_value=None)
def test_run_command(mock_run):
    result = runner.invoke(app, [
        "run", 
        "dataset",
        "--storage-settings", str(TEST_DIR/"settings.toml"),
        "--directory", str(TEST_DIR),
        "--url", EXAMPLE_URL, 
        "--token", "token",
    ])
    assert result.exit_code == 0
    mock_run.assert_called_once()


def mock_call_run(run):
    dataset = models.Dataset.objects.get(slug=run.dataset_slug)
    dataset.locked = True
    dataset.save()


@pytest.mark.django_db
@patch('crunch.client.main.connections.Connection', get_mock_connection )
@patch.object(Run, '__call__', mock_call_run)
def test_next_command():
    ContentType.objects.clear_cache()
    project = models.Project.objects.create(name="Test Project")    
    dataset1 = models.Dataset.objects.create(name="Test Dataset 1", parent=project)    
    dataset2 = models.Dataset.objects.create(name="Test Dataset 2", parent=project)    

    result = runner.invoke(app, [
        "next", 
        "--storage-settings", str(TEST_DIR/"settings.toml"),
        "--directory", str(TEST_DIR),
        "--url", EXAMPLE_URL, 
        "--token", "token",
    ])

    dataset1.refresh_from_db()
    dataset2.refresh_from_db()
    assert dataset1.locked
    assert not dataset2.locked    
    assert result.exit_code == 0


@pytest.mark.django_db
@patch('crunch.client.main.connections.Connection', get_mock_connection )
@patch.object(Run, '__call__', mock_call_run)
def test_loop_command():
    ContentType.objects.clear_cache()
    project = models.Project.objects.create(name="Test Project")    
    dataset1 = models.Dataset.objects.create(name="Test Dataset 1", parent=project)    
    dataset2 = models.Dataset.objects.create(name="Test Dataset 2", parent=project)    

    result = runner.invoke(app, [
        "loop", 
        "--storage-settings", str(TEST_DIR/"settings.toml"),
        "--directory", str(TEST_DIR),
        "--url", EXAMPLE_URL, 
        "--token", "token",
    ])

    dataset1.refresh_from_db()
    dataset2.refresh_from_db()
    assert dataset1.locked
    assert dataset2.locked    
    assert result.exit_code == 0
