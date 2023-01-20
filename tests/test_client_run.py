from unittest.mock import patch
from pathlib import Path
import tempfile
import pytest
from crunch.django.app import models
from crunch.django.app.enums import Stage, State

from django.core.files.storage import FileSystemStorage

from .test_client_connections import MockResponse, MockConnection
from .test_storages import MockSettings, TEST_DIR

from crunch.client import connections, enums
from crunch.client.run import Run

def request_get(url, **kwargs):
    if url == "http://www.example.com/api/datasets/dataset":
        return MockResponse(data=dict(
            slug="dataset",
            parent="project",
            id=2,
            base_file_path=str(TEST_DIR),
        ))
    elif url == "http://www.example.com/api/projects/project":
        return MockResponse(data=dict(
            slug="project",
            parent="project",
            workflow="cat dataset.json",
        ))
    raise ValueError(f"url '{url}' cannot be interpreted.")

@pytest.mark.django_db
@patch('requests.get', request_get)
def test_run_setup():
    project = models.Project.objects.create(name="project")    
    dataset = models.Dataset.objects.create(parent=project, name="dataset")    
    connection = MockConnection(base_url="http://www.example.com", token="token")
    absolute_path = str(TEST_DIR.absolute())
    storage = FileSystemStorage(location=absolute_path, base_url="http://www.example.com")
    
    with patch('crunch.django.app.storages.default_storage', storage):
        with tempfile.TemporaryDirectory() as tmpdir:
            run = Run(
                connection=connection, 
                dataset_slug="dataset", 
                storage_settings={}, 
                working_directory=tmpdir, 
                workflow_type=enums.WorkflowType.script, 
                workflow_path=None, 
            )
            result = run.setup()

            assert result == enums.RunResult.SUCCESS
            assert models.Status.objects.count() == 2
            assert dataset.statuses.count() == 2
            statuses = list(dataset.statuses.all())

            for status in statuses:
                assert status.stage == Stage.SETUP

            assert statuses[0].state == State.START
            assert statuses[1].state == State.SUCCESS

            tmpdir = Path(tmpdir)
            dataset_json_text = (tmpdir/".crunch/dataset.json").read_text()
            assert str(TEST_DIR) in dataset_json_text

            project_json_text = (tmpdir/".crunch/project.json").read_text()
            assert "cat dataset.json" in project_json_text

            script_text = (tmpdir/".crunch/script.sh").read_text()
            assert "cat dataset.json" in script_text


