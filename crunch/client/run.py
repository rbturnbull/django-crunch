from typing import Dict, Union
from datetime import datetime
import requests
from functools import cached_property
from pathlib import Path
import traceback
import subprocess
import json
import shutil
from django.core.files.storage import DefaultStorage

from crunch.django.app.enums import Stage, State
from crunch.django.app import storages
from rich.console import Console

console = Console()
err_console = Console(stderr=True)

from . import utils
from .connections import Connection
from .enums import WorkflowType, RunResult

STAGE_STYLE = "bold magenta"
ERROR_STYLE = "red on white"

def run_subprocess(command:str, working_directory:Path=None) -> int:
    """
    Runs a subprocess.

    Args:
        command (str): The command to run.
        working_directory (Path, optional): The working directory to run the command in. Defaults to None.

    Returns:
        int: The returncode of the subprocess.
    """
    process = subprocess.Popen(
        [command],
        cwd=working_directory,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=False,  # Use shell=True if it is a shell command
    )

    # Read and print stdout while the process is running
    with open(working_directory/"crunch-stdout.log", "w") as f:
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output, end='')
                print(output, end='', file=f, flush=True)

    # Capture and handle stderr
    stderr_output = process.communicate()[1]
    if stderr_output:
        with open(working_directory/"crunch-stderr.log", "w") as f:
            f.write(stderr_output)
    
    if process.returncode != 0:
        raise ChildProcessError(f"Error running {command}: {process.returncode}\n" + stderr_output)

    return process.returncode


class Run():
    """
    An object to manage processing a crunch dataset.
    """
    def __init__(
        self, 
        connection:Connection, 
        dataset_slug:str, 
        storage_settings:Union[Dict,Path], 
        working_directory:Path, 
        workflow_type:WorkflowType, 
        workflow_path:Path=None, 
        download_from_storage:bool=True,
        upload_to_storage:bool=True,
        cleanup:bool=False,
        cores:str="1",
    ):
        self.connection = connection
        self.dataset_slug = dataset_slug

        if not self.dataset_slug:
            raise ValueError("Please specifiy dataset.")

        self.dataset_data = connection.get_json_response(f"/api/datasets/{dataset_slug}/")
        self.workflow_type = workflow_type
        self.workflow_path = workflow_path
        self.cores = cores
        self.storage_settings = storage_settings
        self.setup_md5_checksums = dict()
        self.download_from_storage = download_from_storage
        self.upload_to_storage = upload_to_storage
        self.cleanup = cleanup

        # TODO raise exception
        assert self.dataset_data["slug"] == dataset_slug
        self.project = self.dataset_data["parent"]
        self.dataset_id = self.dataset_data["id"]
        self.base_file_path = self.dataset_data["base_file_path"]

        my_working_directory = Path(working_directory, self.dataset_data["slug"].replace(":", "--"))
        my_working_directory.mkdir(exist_ok=True, parents=True)
        self.working_directory = my_working_directory

    def send_status(self, state, note:str="") -> requests.Response:
        """ Sends a status update about the processing of this dataset. """
        return self.connection.send_status(
            self.dataset_id, 
            stage=self.current_stage, 
            state=state, 
            note=note,
        )

    @cached_property
    def crunch_subdir(self) -> Path:
        """ Returns the path to the .crunch subdirectory in the working directory for this dataset. """
        crunch_subdir = self.working_directory/".crunch"        
        crunch_subdir.mkdir(exist_ok=True, parents=True)
        return crunch_subdir

    @cached_property
    def storage(self) -> DefaultStorage:
        """ Gets the default storage object. """
        return storages.get_storage_with_settings(self.storage_settings)

    def setup(self) -> RunResult:
        """ 
        Sets up this dataset for processing.
        
        This involves:

        - Copying the initial data from storage
        - Saving the MD5 checksums for all the initial data in ``.crunch/setup_md5_checksums.json``
        - Saves the metadata for the dataset in ``.crunch/dataset.json``
        - Saves the metadata for the project in ``.crunch/project.json``
        - Creates the script to run the workflow (either a bash script or a Snakefile for Snakemake)


        Returns:
            RunResult: Whether or not this stage was successful.
        """
        self.current_stage = Stage.SETUP
        console.print(f"Setup stage {self.dataset_slug}", style=STAGE_STYLE)
        try:
            self.send_status(State.START)
            
            # Pull data from storage
            if self.download_from_storage:
                storages.copy_recursive_from_storage(
                    self.base_file_path, self.working_directory, storage=self.storage
                )
                self.setup_md5_checksums = utils.md5_checksums(self.working_directory)
                with open(self.crunch_subdir / "setup_md5_checksums.json", "w", encoding="utf-8") as f:
                    json.dump(self.setup_md5_checksums, f, ensure_ascii=False, indent=4)

            # TODO check to see if dataset.json already exists
            with open(self.crunch_subdir / "dataset.json", "w", encoding="utf-8") as f:
                json.dump(self.dataset_data, f, ensure_ascii=False, indent=4)

            # get project details
            project_data = self.connection.get_json_response(f"/api/projects/{self.project}/")
            # TODO raise exception
            assert project_data["slug"] == self.project

            # TODO check to see if project.json already exists
            with open(self.crunch_subdir / "project.json", "w", encoding="utf-8") as f:
                json.dump(project_data, f, ensure_ascii=False, indent=4)

            # get snakefile or script
            if not self.workflow_path:
                self.workflow_path = utils.write_workflow(
                    project_data["workflow"], 
                    working_directory=self.crunch_subdir,
                    workflow_type=self.workflow_type,
                )

            self.send_status(State.SUCCESS)
            console.print(f"Setup success {self.dataset_slug}", style=STAGE_STYLE)
        except Exception as e:
            err_console.print(f"Setup failed {self.dataset_slug}: {e}", style=STAGE_STYLE)
            self.send_status(State.FAIL, note=str(e))
            return RunResult.FAIL
        
        return RunResult.SUCCESS

    def workflow(self) -> RunResult:
        """ 
        Runs the workflow on a dataset that has been set up.
        
        This involves running a bash script as a subprocess or running Snakemake with a Snakefile.

        Returns:
            RunResult: Whether or not this stage was successful.
        """
        self.current_stage = Stage.WORKFLOW
        console.print(f"Workflow stage {self.dataset_slug}", style=STAGE_STYLE)
        try:
            self.send_status(State.START)
            if self.workflow_type == WorkflowType.snakemake:
                import snakemake

                args = [
                    f"--snakefile={self.workflow_path}",
                    "--use-conda",
                    f"--cores={self.cores}",
                    f"--directory={self.working_directory}",
                    f"--conda-frontend={utils.conda_frontend()}"
                ]

                try:
                    snakemake.main(args)
                except SystemExit as result:
                    print(f"result {result}")
            elif self.workflow_type == WorkflowType.script:
                run_subprocess(f"{self.workflow_path.resolve()}", working_directory=self.working_directory)

            self.send_status(State.SUCCESS)
            console.print(f"Workflow success {self.dataset_slug}", style=STAGE_STYLE)
        except Exception as e:
            err_console.print(f"Workflow failed {self.dataset_slug}: {e}", style=STAGE_STYLE)
            self.send_status(State.FAIL, note=str(e))
            return RunResult.FAIL
        
        return RunResult.SUCCESS

    def upload(self) -> RunResult:
        """
        Uploads new or modified files to the storage for the dataset.

        It also creates the following files:
        - .crunch/upload_md5_checksums.json which lists all MD5 checksums after the dataset has finished.
        - .crunch/deleted.txt which lists all files that were present after setup but which were deleted as the workflow ran.

        Returns:
            RunResult: Whether or not this stage was successful.
        """
        self.current_stage = Stage.UPLOAD
        console.print(f"Upload stage {self.dataset_slug}", style=STAGE_STYLE)
        try:
            self.send_status(State.START)

            if self.upload_to_storage:
                # calculate checksums
                self.upload_md5_checksums = utils.md5_checksums(self.working_directory)
                upload_md5_checksums_path = self.crunch_subdir / "upload_md5_checksums.json"
                with open(upload_md5_checksums_path, "w", encoding="utf-8") as f:
                    json.dump(self.upload_md5_checksums, f, ensure_ascii=False, indent=4)

                setup_files = set(self.setup_md5_checksums.keys())
                upload_files = set(self.upload_md5_checksums.keys())
                new_files = upload_files - setup_files
                deleted_files = setup_files - upload_files
                remaining_files = setup_files.intersection(upload_files)
                modified_files = set(
                    file for file in remaining_files 
                    if self.upload_md5_checksums[file] != self.setup_md5_checksums[file]
                )
                deleted_log_path = self.crunch_subdir / "deleted.txt"
                deleted_log_path.write_text("\n".join(deleted_files))

                files_to_upload = modified_files | new_files | set([upload_md5_checksums_path, deleted_log_path])
                paths_to_upload = [self.working_directory/file for file in files_to_upload]

                storages.copy_to_storage(
                    paths_to_upload, 
                    local_dir=self.working_directory,
                    base=self.base_file_path, 
                    storage=self.storage,
                )

            # Option to delete on remote storage?
            if self.cleanup:
                shutil.rmtree(self.working_directory)	

            self.send_status(State.SUCCESS)
            console.print(f"Upload success {self.dataset_slug}", style=STAGE_STYLE)
        except Exception as e:
            err_console.print(f"Upload failed {self.dataset_slug}: {e}", style=STAGE_STYLE)
            self.send_status(State.FAIL, note=str(e))
            return RunResult.FAIL
        
        return RunResult.SUCCESS

    def __call__(self) -> RunResult:
        console.print(f"Processing '{self.dataset_slug}'.")
        self.setup_result = self.setup()
        if self.setup_result:
            return self.setup_result

        self.workflow_result = self.workflow()
        if self.workflow_result:
            return self.workflow_result

        self.upload_result = self.upload()
        return self.upload_result

