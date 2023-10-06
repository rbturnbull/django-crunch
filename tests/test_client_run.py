from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest
import pytest
from crunch.django.app import models
from crunch.django.app.enums import Stage, State

from django.core.files.storage import FileSystemStorage

from crunch.client import enums
from crunch.client.run import Run
from crunch.django.app import storages

from .test_client_connections import MockResponse, MockConnection
from .test_storages import MockSettings, TEST_DIR, assert_test_data
from .test_client_utils import raise_called_process_error


def mock_snakemake_main(args):
    assert "--use-conda" in args
    raise SystemExit


def save_fail(*args, **kwargs):
    raise FileNotFoundError("This file does not exist.") # force exception


def raise_system_error(*args, **kwargs):
    raise SystemError("Mock System Error")


def request_get(url, **kwargs):
    if url == "http://www.example.com/api/datasets/dataset/":
        return MockResponse(data=dict(
            slug="dataset",
            parent="project",
            id=2,
            base_file_path=str(TEST_DIR),
        ))
    elif url == "http://www.example.com/api/projects/project/":
        return MockResponse(data=dict(
            slug="project",
            parent="project",
            workflow="cat .crunch/dataset.json",
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


# @patch('requests.get', request_get)
class TestRun(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def setUp(self):
        super().setUp()
        self.connection = MockConnection(base_url="http://www.example.com", token="token") # ensure first
        self.project = models.Project.objects.create(name="project", workflow="cat .crunch/dataset.json")    
        self.dataset = models.Dataset.objects.create(parent=self.project, name="dataset", base_file_path=str(TEST_DIR))    
        self.absolute_path = str(TEST_DIR.absolute())
        self.storage = FileSystemStorage(location=self.absolute_path, base_url="http://www.example.com")

    @pytest.mark.django_db
    def test_run_setup_script(self):
        with patch('crunch.django.app.storages.default_storage', self.storage):
            with tempfile.TemporaryDirectory() as tmpdir:
                run = Run(
                    connection=self.connection, 
                    dataset_slug="project:dataset", 
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

                tmpdir = Path(tmpdir, "project--dataset")
                dataset_json_text = (tmpdir/".crunch/dataset.json").read_text()
                assert str(TEST_DIR) in dataset_json_text

                project_json_text = (tmpdir/".crunch/project.json").read_text()
                assert "cat .crunch/dataset.json" in project_json_text

                script_text = (tmpdir/".crunch/script.sh").read_text()
                assert "cat .crunch/dataset.json" in script_text

                assert_test_data(tmpdir)

    @patch('json.dump', raise_system_error)
    @pytest.mark.django_db
    def test_run_setup_script_fail(self):
        with patch('crunch.django.app.storages.default_storage', self.storage):
            with tempfile.TemporaryDirectory() as tmpdir:
                run = Run(
                    connection=self.connection, 
                    dataset_slug="project:dataset", 
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
                    dataset_slug="project:dataset", 
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

                tmpdir = Path(tmpdir, "project--dataset")
                dataset_json_text = (tmpdir/".crunch/dataset.json").read_text()
                assert str(TEST_DIR) in dataset_json_text

                project_json_text = (tmpdir/".crunch/project.json").read_text()
                assert "cat .crunch/dataset.json" in project_json_text

                snakefile_text = (tmpdir/".crunch/Snakefile").read_text()
                assert "cat .crunch/dataset.json" in snakefile_text

                assert_test_data(tmpdir)

    @pytest.mark.django_db
    def test_run_workflow_script(self):
        with patch('crunch.django.app.storages.default_storage', self.storage):
            with tempfile.TemporaryDirectory() as tmpdir:
                run = Run(
                    connection=self.connection, 
                    dataset_slug="project:dataset", 
                    storage_settings={}, 
                    working_directory=tmpdir, 
                    workflow_type=enums.WorkflowType.script, 
                    workflow_path=Path(TEST_DIR, "dummy-workflow"), 
                )

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
    @patch('snakemake.main', mock_snakemake_main )
    def test_run_workflow_snakemake(self):
        with patch('crunch.django.app.storages.default_storage', self.storage):
            with tempfile.TemporaryDirectory() as tmpdir:
                run = Run(
                    connection=self.connection, 
                    dataset_slug="project:dataset", 
                    storage_settings={}, 
                    working_directory=tmpdir, 
                    workflow_type=enums.WorkflowType.snakemake, 
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
    def test_run_workflow_script_fail(self):
        with patch('crunch.django.app.storages.default_storage', self.storage):
            with tempfile.TemporaryDirectory() as tmpdir:
                run = Run(
                    connection=self.connection, 
                    dataset_slug="project:dataset", 
                    storage_settings={}, 
                    working_directory=tmpdir, 
                    workflow_type=enums.WorkflowType.script, 
                    workflow_path=Path(TEST_DIR)/"dummy-workflow-fail", 
                )
                result = run.workflow()
                captured = self.capsys.readouterr()
                assert "Workflow stage project:dataset\nDummy Workflow\n" in captured.out
                assert "Workflow failed project:dataset: Error running" in captured.err
                assert "tests/test-data/dummy-workflow-fail: 42\nError message 42!" in captured.err

                stdout_file = Path(tmpdir)/"project--dataset"/"crunch-stdout.log"
                stderr_file = Path(tmpdir)/"project--dataset"/"crunch-stderr.log"

                assert stdout_file.exists()
                assert "Dummy Workflow" in stdout_file.read_text()
                assert stderr_file.exists()
                assert "Error message 42!" in stderr_file.read_text()

                assert result == enums.RunResult.FAIL
                assert models.Status.objects.count() == 2
                assert self.dataset.statuses.count() == 2
                statuses = list(self.dataset.statuses.all())

                assert "Error message 42!" in self.dataset.statuses.last().note

                for status in statuses:
                    assert status.stage == Stage.WORKFLOW

                assert statuses[0].state == State.START
                assert statuses[1].state == State.FAIL


@patch('requests.get', request_get)
class TestRunNoStorage(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.connection = MockConnection(base_url="http://www.example.com", token="token") # ensure first
        self.project = models.Project.objects.create(name="project", workflow="cat .crunch/dataset.json")    
        self.dataset = models.Dataset.objects.create(parent=self.project, name="dataset", base_file_path=str(TEST_DIR))    

    @pytest.mark.django_db
    def test_run_upload(self):
        with tempfile.TemporaryDirectory() as remote_dir:
            remote_dir = Path(remote_dir)
            storage = FileSystemStorage(location=remote_dir.absolute(), base_url="http://www.example.com")
            
            # copy files from test data to mock remote store
            storages.copy_recursive_to_storage(TEST_DIR, "./", storage=storage)

            with tempfile.TemporaryDirectory() as local_dir:
                local_dir = Path(local_dir)

                with patch('crunch.django.app.storages.default_storage', storage):
                    run = Run(
                        connection=self.connection, 
                        dataset_slug="project:dataset", 
                        storage_settings={}, 
                        working_directory=local_dir,
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

                    assert_test_data(remote_dir)

    @pytest.mark.django_db
    def test_run_upload_fail(self):
        with tempfile.TemporaryDirectory() as remote_dir:
            remote_dir = Path(remote_dir)
            storage = FileSystemStorage(location=remote_dir.absolute(), base_url="http://www.example.com")
            
            # copy files from test data to mock remote store
            storages.copy_recursive_to_storage(TEST_DIR, "./", storage=storage)

            storage._save = save_fail

            with tempfile.TemporaryDirectory() as local_dir:
                local_dir = Path(local_dir)

                with patch('crunch.django.app.storages.default_storage', storage):
                    run = Run(
                        connection=self.connection, 
                        dataset_slug="project:dataset", 
                        storage_settings={}, 
                        working_directory=local_dir,
                        workflow_type=enums.WorkflowType.script, 
                        workflow_path=Path(TEST_DIR, "dummy-workflow"), 
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

    @pytest.mark.django_db
    def test_run_all(self):
        with tempfile.TemporaryDirectory() as remote_dir:
            remote_dir = Path(remote_dir)
            storage = FileSystemStorage(location=remote_dir.absolute(), base_url="http://www.example.com")
            
            # copy files from test data to mock remote store
            storages.copy_recursive_to_storage(TEST_DIR, "./", storage=storage)

            with tempfile.TemporaryDirectory() as local_dir:
                local_dir = Path(local_dir)

                with patch('crunch.django.app.storages.default_storage', storage):
                    run = Run(
                        connection=self.connection, 
                        dataset_slug="project:dataset", 
                        storage_settings={}, 
                        working_directory=local_dir,
                        workflow_type=enums.WorkflowType.script, 
                        workflow_path=Path(TEST_DIR, "dummy-workflow"), 
                    )
                    run.base_file_path = remote_dir
                    result = run()

                    statuses = list(self.dataset.statuses.all())

                    assert result == enums.RunResult.SUCCESS
                    assert models.Status.objects.count() == 6
                    assert self.dataset.statuses.count() == 6

                    assert statuses[0].state == State.START
                    assert statuses[1].state == State.SUCCESS
                    assert statuses[2].state == State.START
                    assert statuses[3].state == State.SUCCESS
                    assert statuses[4].state == State.START
                    assert statuses[5].state == State.SUCCESS

                    assert statuses[0].stage == Stage.SETUP
                    assert statuses[1].stage == Stage.SETUP
                    assert statuses[2].stage == Stage.WORKFLOW
                    assert statuses[3].stage == Stage.WORKFLOW
                    assert statuses[4].stage == Stage.UPLOAD
                    assert statuses[5].stage == Stage.UPLOAD

                    dataset_json_text = (remote_dir/".crunch/dataset.json").read_text()
                    assert str(TEST_DIR) in dataset_json_text

                    project_json_text = (remote_dir/".crunch/project.json").read_text()
                    assert "cat .crunch/dataset.json" in project_json_text

                    # script_text = (remote_dir/".crunch/script.sh").read_text()
                    # assert "cat .crunch/dataset.json" in script_text

                    assert_test_data(remote_dir)

    @pytest.mark.django_db
    @patch('json.dump', raise_system_error)
    def test_run_all_setup_fail(self):
        with tempfile.TemporaryDirectory() as remote_dir:
            remote_dir = Path(remote_dir)
            storage = FileSystemStorage(location=remote_dir.absolute(), base_url="http://www.example.com")
            
            # copy files from test data to mock remote store
            storages.copy_recursive_to_storage(TEST_DIR, "./", storage=storage)

            with tempfile.TemporaryDirectory() as local_dir:
                local_dir = Path(local_dir)

                with patch('crunch.django.app.storages.default_storage', storage):
                    run = Run(
                        connection=self.connection, 
                        dataset_slug="project:dataset", 
                        storage_settings={}, 
                        working_directory=local_dir,
                        workflow_type=enums.WorkflowType.script, 
                        workflow_path=None, 
                    )
                    run.base_file_path = remote_dir
                    result = run()

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
    @patch("subprocess.run", raise_called_process_error )
    def test_run_all_workflow_fail(self):
        with tempfile.TemporaryDirectory() as remote_dir:
            remote_dir = Path(remote_dir)
            storage = FileSystemStorage(location=remote_dir.absolute(), base_url="http://www.example.com")
            
            # copy files from test data to mock remote store
            storages.copy_recursive_to_storage(TEST_DIR, "./", storage=storage)

            with tempfile.TemporaryDirectory() as local_dir:
                local_dir = Path(local_dir)

                with patch('crunch.django.app.storages.default_storage', storage):
                    run = Run(
                        connection=self.connection, 
                        dataset_slug="project:dataset", 
                        storage_settings={}, 
                        working_directory=local_dir,
                        workflow_type=enums.WorkflowType.script, 
                        workflow_path=None, 
                    )
                    run.base_file_path = remote_dir
                    result = run()

                assert result == enums.RunResult.FAIL
                assert models.Status.objects.count() == 4
                assert self.dataset.statuses.count() == 4
                statuses = list(self.dataset.statuses.all())

                assert statuses[0].state == State.START
                assert statuses[1].state == State.SUCCESS
                assert statuses[2].state == State.START
                assert statuses[3].state == State.FAIL

                assert statuses[0].stage == Stage.SETUP
                assert statuses[1].stage == Stage.SETUP
                assert statuses[2].stage == Stage.WORKFLOW
                assert statuses[3].stage == Stage.WORKFLOW

    @pytest.mark.django_db
    def test_run_all_upload_fail(self):
        with tempfile.TemporaryDirectory() as remote_dir:
            remote_dir = Path(remote_dir)
            storage = FileSystemStorage(location=remote_dir.absolute(), base_url="http://www.example.com")
            
            # copy files from test data to mock remote store
            storages.copy_recursive_to_storage(TEST_DIR, "./", storage=storage)

            storage._save = save_fail

            with tempfile.TemporaryDirectory() as local_dir:
                local_dir = Path(local_dir)

                with patch('crunch.django.app.storages.default_storage', storage):
                    run = Run(
                        connection=self.connection, 
                        dataset_slug="project:dataset", 
                        storage_settings={}, 
                        working_directory=local_dir,
                        workflow_type=enums.WorkflowType.script, 
                        workflow_path=Path(TEST_DIR, "dummy-workflow"), 
                    )
                    run.base_file_path = remote_dir
                    result = run()

                    assert result == enums.RunResult.FAIL
                    assert models.Status.objects.count() == 6
                    assert self.dataset.statuses.count() == 6
                    statuses = list(self.dataset.statuses.all())

                    assert statuses[0].state == State.START
                    assert statuses[1].state == State.SUCCESS
                    assert statuses[2].state == State.START
                    assert statuses[3].state == State.SUCCESS
                    assert statuses[4].state == State.START
                    assert statuses[5].state == State.FAIL

                    assert statuses[0].stage == Stage.SETUP
                    assert statuses[1].stage == Stage.SETUP
                    assert statuses[2].stage == Stage.WORKFLOW
                    assert statuses[3].stage == Stage.WORKFLOW
                    assert statuses[4].stage == Stage.UPLOAD
                    assert statuses[5].stage == Stage.UPLOAD
