from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest
import pytest
from crunch.django.app import models
from crunch.django.app.enums import Stage, State

from django.core.files.storage import FileSystemStorage

from crunch.client import connections, enums
from crunch.client.run import Run

from .test_client_connections import MockResponse, MockConnection
from .test_storages import MockSettings, TEST_DIR, assert_test_data
from .test_client_utils import raise_called_process_error


def mock_snakemake_main(*args):
    assert "--use-conda" in args
    raise SystemExit


def raise_system_error(*args, **kwargs):
    raise SystemError("Mock System Error")


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


def test_run_blank_dataset_slug():
    with pytest.raises(ValueError, match=r"Please specifiy dataset"):
        Run(
            connection=None, 
            dataset_slug="", 
            storage_settings={}, 
            working_directory=None, 
            workflow_type=enums.WorkflowType.script, 
            workflow_path=None, 
        )


@patch('requests.get', request_get)
class TestRun(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.connection = MockConnection(base_url="http://www.example.com", token="token") # ensure first
        self.project = models.Project.objects.create(name="project")    
        self.dataset = models.Dataset.objects.create(parent=self.project, name="dataset")    
        self.absolute_path = str(TEST_DIR.absolute())
        self.storage = FileSystemStorage(location=self.absolute_path, base_url="http://www.example.com")

    @pytest.mark.django_db
    def test_run_setup_script(self):
        with patch('crunch.django.app.storages.default_storage', self.storage):
            with tempfile.TemporaryDirectory() as tmpdir:
                run = Run(
                    connection=self.connection, 
                    dataset_slug="dataset", 
                    storage_settings={}, 
                    working_directory=tmpdir, 
                    workflow_type=enums.WorkflowType.script, 
                    workflow_path=None, 
                )
                result = run.setup()

                assert result == enums.RunResult.SUCCESS
                assert models.Status.objects.count() == 2
                assert self.dataset.statuses.count() == 2
                statuses = list(self.dataset.statuses.all())

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

                assert_test_data(tmpdir)

    @patch('json.dump', raise_system_error)
    @pytest.mark.django_db
    def test_run_setup_script_fail(self):
        with patch('crunch.django.app.storages.default_storage', self.storage):
            with tempfile.TemporaryDirectory() as tmpdir:
                run = Run(
                    connection=self.connection, 
                    dataset_slug="dataset", 
                    storage_settings={}, 
                    working_directory=tmpdir, 
                    workflow_type=enums.WorkflowType.script, 
                    workflow_path=None, 
                )
                result = run.setup()

                assert result == enums.RunResult.FAIL
                assert models.Status.objects.count() == 2
                assert self.dataset.statuses.count() == 2
                statuses = list(self.dataset.statuses.all())

                for status in statuses:
                    assert status.stage == Stage.SETUP

                assert statuses[0].state == State.START
                assert statuses[1].state == State.FAIL
                assert statuses[1].note == "Mock System Error"

    @pytest.mark.django_db
    def test_run_setup_snakemake(self):
        with patch('crunch.django.app.storages.default_storage', self.storage):
            with tempfile.TemporaryDirectory() as tmpdir:
                run = Run(
                    connection=self.connection, 
                    dataset_slug="dataset", 
                    storage_settings={}, 
                    working_directory=tmpdir, 
                    workflow_type=enums.WorkflowType.snakemake, 
                    workflow_path=None, 
                )
                result = run.setup()

                assert result == enums.RunResult.SUCCESS
                assert models.Status.objects.count() == 2
                assert self.dataset.statuses.count() == 2
                statuses = list(self.dataset.statuses.all())

                for status in statuses:
                    assert status.stage == Stage.SETUP

                assert statuses[0].state == State.START
                assert statuses[1].state == State.SUCCESS

                tmpdir = Path(tmpdir)
                dataset_json_text = (tmpdir/".crunch/dataset.json").read_text()
                assert str(TEST_DIR) in dataset_json_text

                project_json_text = (tmpdir/".crunch/project.json").read_text()
                assert "cat dataset.json" in project_json_text

                snakefile_text = (tmpdir/".crunch/Snakefile").read_text()
                assert "cat dataset.json" in snakefile_text

                assert_test_data(tmpdir)

    @pytest.mark.django_db
    @patch('subprocess.run', lambda *args, **kwargs: 0 )
    def test_run_workflow_script(self):
        with patch('crunch.django.app.storages.default_storage', self.storage):
            with tempfile.TemporaryDirectory() as tmpdir:
                run = Run(
                    connection=self.connection, 
                    dataset_slug="dataset", 
                    storage_settings={}, 
                    working_directory=tmpdir, 
                    workflow_type=enums.WorkflowType.script, 
                    workflow_path=None, 
                )
                run.workflow_path = Path(tmpdir)/"dummy_workflow"
                result = run.workflow()

                assert result == enums.RunResult.SUCCESS
                assert models.Status.objects.count() == 2
                assert self.dataset.statuses.count() == 2
                statuses = list(self.dataset.statuses.all())

                for status in statuses:
                    assert status.stage == Stage.WORKFLOW

                assert statuses[0].state == State.START
                assert statuses[1].state == State.SUCCESS


    @pytest.mark.django_db
    @patch('subprocess.run', lambda *args, **kwargs: 0 )
    @patch('snakemake.main', return_value=mock_snakemake_main )
    def test_run_workflow_snakemake(self, mock_snakemake):
        with patch('crunch.django.app.storages.default_storage', self.storage):
            with tempfile.TemporaryDirectory() as tmpdir:
                run = Run(
                    connection=self.connection, 
                    dataset_slug="dataset", 
                    storage_settings={}, 
                    working_directory=tmpdir, 
                    workflow_type=enums.WorkflowType.snakemake, 
                    workflow_path=None, 
                )
                run.workflow_path = Path(tmpdir)/"dummy_workflow"
                result = run.workflow()

                mock_snakemake.assert_called_once()
                assert result == enums.RunResult.SUCCESS
                assert models.Status.objects.count() == 2
                assert self.dataset.statuses.count() == 2
                statuses = list(self.dataset.statuses.all())

                for status in statuses:
                    assert status.stage == Stage.WORKFLOW

                assert statuses[0].state == State.START
                assert statuses[1].state == State.SUCCESS


    @pytest.mark.django_db
    @patch("subprocess.run", raise_called_process_error )
    def test_run_workflow_script_fail(self):
        with patch('crunch.django.app.storages.default_storage', self.storage):
            with tempfile.TemporaryDirectory() as tmpdir:
                run = Run(
                    connection=self.connection, 
                    dataset_slug="dataset", 
                    storage_settings={}, 
                    working_directory=tmpdir, 
                    workflow_type=enums.WorkflowType.script, 
                    workflow_path=None, 
                )
                run.workflow_path = Path(tmpdir)/"dummy_workflow"
                result = run.workflow()

                assert result == enums.RunResult.FAIL
                assert models.Status.objects.count() == 2
                assert self.dataset.statuses.count() == 2
                statuses = list(self.dataset.statuses.all())

                for status in statuses:
                    assert status.stage == Stage.WORKFLOW

                assert statuses[0].state == State.START
                assert statuses[1].state == State.FAIL


@patch('requests.get', request_get)
class TestRunUpload(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.connection = MockConnection(base_url="http://www.example.com", token="token") # ensure first
        self.project = models.Project.objects.create(name="project")    
        self.dataset = models.Dataset.objects.create(parent=self.project, name="dataset")    

    @pytest.mark.django_db
    def test_run_upload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            storage = FileSystemStorage(location=tmpdir.absolute(), base_url="http://www.example.com")
            with patch('crunch.django.app.storages.default_storage', storage):
                run = Run(
                    connection=self.connection, 
                    dataset_slug="dataset", 
                    storage_settings={}, 
                    working_directory=TEST_DIR,  
                    workflow_type=enums.WorkflowType.script, 
                    workflow_path=None, 
                )
                run.base_file_path = "."
                result = run.upload()

                assert result == enums.RunResult.SUCCESS
                assert models.Status.objects.count() == 2
                assert self.dataset.statuses.count() == 2
                statuses = list(self.dataset.statuses.all())

                for status in statuses:
                    assert status.stage == Stage.UPLOAD

                assert statuses[0].state == State.START
                assert statuses[1].state == State.SUCCESS

                assert_test_data(tmpdir)

    @pytest.mark.django_db
    def test_run_upload_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            storage = FileSystemStorage(location=tmpdir.absolute(), base_url="http://www.example.com")
            def save_fail(*args, **kwargs):
                raise FileNotFoundError("This file does not exist.") # force exception

            storage._save = save_fail
            with patch('crunch.django.app.storages.default_storage', storage):
                run = Run(
                    connection=self.connection, 
                    dataset_slug="dataset", 
                    storage_settings={}, 
                    working_directory=TEST_DIR,
                    workflow_type=enums.WorkflowType.script, 
                    workflow_path=None, 
                )
                run.base_file_path = "."
                result = run.upload()

                assert result == enums.RunResult.FAIL
                assert models.Status.objects.count() == 2
                assert self.dataset.statuses.count() == 2
                statuses = list(self.dataset.statuses.all())

                for status in statuses:
                    assert status.stage == Stage.UPLOAD

                assert statuses[0].state == State.START
                assert statuses[1].state == State.FAIL
                assert statuses[1].note == "This file does not exist."


    