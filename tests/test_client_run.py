from unittest.mock import patch
import tempfile

from django.core.files.storage import FileSystemStorage

from .test_client_connections import MockResponse
from .test_storages import MockSettings, TEST_DIR

from crunch.client import connections, enums
from crunch.client.run import Run

def request_get(url, **kwargs):
    if url == "http://www.example.com/api/datasets/dataset":
        return MockResponse(data=dict(
            slug="dataset",
            parent="project",
            id=2,
            base_file_path=TEST_DIR,
        ))
    elif url == "http://www.example.com/api/projects/project":
        return MockResponse(data=dict(
            slug="project",
            parent="project",
            workflow="cat dataset.json",
        ))
    raise ValueError(f"url '{url}' cannot be interpreted.")


@patch('requests.get', request_get)
def test_run_setup():
    breakpoint()
    connection = connections.Connection(base_url="http://www.example.com", token="token")
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
            run.setup()