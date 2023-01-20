from typing import Dict, Union
import requests
from functools import cached_property
from pathlib import Path
import traceback
import subprocess
import json
from django.core.files.storage import DefaultStorage

from crunch.django.app.enums import Stage, State
from crunch.django.app import storages
from rich.console import Console

console = Console()

from . import utils
from .connections import Connection
from .enums import WorkflowType, RunResult

STAGE_STYLE = "bold red"

class Run():
    def __init__(
        self, 
        connection:Connection, 
        dataset_slug:str, 
        storage_settings:Union[Dict,Path], 
        working_directory:Path, 
        workflow_type:WorkflowType, 
        workflow_path:Path=None, 
        cores:str="1",
    ):
        self.connection = connection
        self.dataset_slug = dataset_slug

        if not self.dataset_slug:
            raise ValueError("Please specifiy dataset.")

        self.dataset_data = connection.get_json_response(f"/api/datasets/{dataset_slug}")
        self.workflow_type = workflow_type
        self.workflow_path = workflow_path
        self.cores = cores
        self.storage_settings = storage_settings

        working_directory = Path(working_directory)
        working_directory.mkdir(exist_ok=True, parents=True)
        self.working_directory = working_directory
        
        # TODO raise exception
        assert self.dataset_data["slug"] == dataset_slug
        self.project = self.dataset_data["parent"]
        self.dataset_id = self.dataset_data["id"]
        self.base_file_path = self.dataset_data["base_file_path"]

    def send_status(self, state, note:str="") -> requests.Response:
        return self.connection.send_status(
            self.dataset_id, 
            stage=self.current_stage, 
            state=state, 
            note=note,
        )

    @cached_property
    def crunch_subdir(self):
        crunch_subdir = self.working_directory/".crunch"        
        crunch_subdir.mkdir(exist_ok=True, parents=True)
        return crunch_subdir

    @cached_property
    def storage(self) -> DefaultStorage:
        return storages.get_storage_with_settings(self.storage_settings)

    def setup(self) -> RunResult:
        self.current_stage = Stage.SETUP
        console.print(f"Setup stage {self.dataset_slug}", style=STAGE_STYLE)
        try:
            self.send_status(State.START)
            
            # Pull data from storage
            storages.copy_recursive_from_storage(
                self.base_file_path, self.working_directory, storage=self.storage
            )

            # TODO check to see if dataset.json already exists
            with open(self.crunch_subdir / "dataset.json", "w", encoding="utf-8") as f:
                json.dump(self.dataset_data, f, ensure_ascii=False, indent=4)

            # get project details
            project_data = self.connection.get_json_response(f"/api/projects/{self.project}")
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
        except Exception as e:
            console.print(f"Setup failed {self.dataset_slug}: {e}", style=STAGE_STYLE)
            self.send_status(State.FAIL, note=str(e))
            return RunResult.FAIL
        
        return RunResult.SUCCESS

    def workflow(self) -> RunResult:
        self.current_stage = Stage.WORKFLOW

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
                subprocess.run(f"{self.workflow_path.resolve()}", capture_output=True, check=True, cwd=self.working_directory)

            self.send_status(State.SUCCESS)
        except Exception as e:
            console.print(f"Workflow failed {self.dataset_slug}: {e}", style=STAGE_STYLE)
            self.send_status(State.FAIL, note=str(e))
            return RunResult.FAIL
        
        return RunResult.SUCCESS

    def upload(self) -> RunResult:
        self.current_stage = Stage.UPLOAD
        console.print(f"Upload stage {self.dataset_slug}", style=STAGE_STYLE)
        try:
            self.send_status(State.START)
            storages.copy_recursive_to_storage(
                self.working_directory, 
                self.base_file_path, 
                storage=self.storage
            )
            self.send_status(State.SUCCESS)
        except Exception as e:
            console.print(f"Upload failed {self.dataset_slug}: {e}", style=STAGE_STYLE)
            traceback.print_exc()
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

        self.upload_result = self.workflow()
        return self.upload_result

