import json
from pathlib import Path
from typing import Optional
from typing import List
import typer
import subprocess
from rich.console import Console

console = Console()

from . import connections
from .diagnostics import get_diagnostics

from crunch.django.app.enums import Stage, State

class NoDatasets(Exception):
    """ Raised when there are no more datasets to process on a crunch site. """
    pass


app = typer.Typer()

url_arg = typer.Argument(..., envvar="CRUNCH_URL", help="The URL for the endpoint for the project on the hosted site.")
token_arg = typer.Argument(..., envvar="CRUNCH_TOKEN", help="An access token for a user on the hosted site.")

@app.command()
def run(
    project:str,
    dataset:str,
    url:str = url_arg,
    token:str = token_arg,
    directory:Path = None,
    cores:str = "1",
):
    """
    Processes a dataset.
    """
    if not dataset:
        return

    console.print(f"Processing '{dataset}' from project '{project}' at {url}.")

    # Create temporary dir
    directory = directory or Path('tmp')
    directory.mkdir(exist_ok=True, parents=True)
    console.print(f"Using temporary directory '{directory}'.")

    # TODO Check to see if there is an old dataset.json

    # get dataset details
    dataset_data = connections.get_json_response( url, f"/api/datasets/{dataset}", token )
    # TODO raise exception
    assert dataset_data['slug'] == dataset
    assert project in dataset_data['project']
    dataset_id = dataset_data['id']

    #############################
    ##       Setup Stage
    #############################
    stage = Stage.SETUP
    try:
        connections.send_status( url, dataset_id, token, stage=stage, state=State.START)
        with open(directory/'project.json', 'w', encoding='utf-8') as f:
            json.dump(dataset_data, f, ensure_ascii=False, indent=4)

        # get project details
        project_data = connections.get_json_response( url, f"/api/projects/{project}", token )
        # TODO raise exception
        assert project_data['slug'] == project
        with open(directory/'project.json', 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=4)

        # pull data

        # get snakefile
        with open(directory/'Snakefile', 'w', encoding='utf-8') as f:
            f.write(project_data['snakefile'])

        connections.send_status( url, dataset_id, token, stage=stage, state=State.SUCCESS)
    except Exception as e:
        connections.send_status( url, dataset_id, token, stage=stage, state=State.FAIL, note=str(e))

    #############################
    ##       Workflow Stage
    #############################

    stage = Stage.WORKFLOW
    try:
        connections.send_status( url, dataset_id, token, stage=stage, state=State.START)
        result = subprocess.Popen(["snakemake", "--cores", cores], cwd=directory)
        if result:
            raise Exception("Workflow failed")
        connections.send_status( url, dataset_id, token, stage=stage, state=State.SUCCESS)
    except Exception as e:
        connections.send_status( url, dataset_id, token, stage=stage, state=State.FAIL, note=str(e))

    #############################
    ##       Upload Stage
    #############################
    stage = Stage.UPLOAD

    # notify

    # print(result)
    return dataset_data


@app.command()
def next(
    url:str = url_arg,
    token:str = token_arg,
    directory:Path = None,
    cores:str = "1",
):
    """
    Processes the next dataset in a project.
    """
    console.print(f"Processing the next dataset from {url}")
    next = connections.get_json_response( url, f"api/next/", token )
    if 'dataset' in next and 'project' in next and next['project'] and next['dataset']:
        return run(project=next['project'], dataset=next['dataset'], url=url, token=token, directory=directory, cores=cores)
    else:
        console.print("No more datasets to process.")


@app.command()
def loop(
    url:str = url_arg,
    token:str = token_arg,
    directory:Path = None,
    cores:str = "1",
):
    """
    Loops through all the datasets in a project and stops when complete.
    """
    console.print(f"Looping through all the datasets from {url} and will stop when complete.")
    while True:
        result = next(url=url, token=token, directory=directory, cores=cores)
        if result is None:
            console.print("Loop concluded.")
            break


@app.command()
def add_project(
    project:str,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new project to the hosted site.
    """
    console.print(f"Adding project '{project}' on the hosted site {url}.")


@app.command()
def add_dataset(
    dataset:str,
    project:str,
    url:str = url_arg,
    token:str = token_arg,
    description:str = "",
    details:str = "",
    verbose:bool = True,
):
    """
    Adds a new dataset to a project on the hosted site.
    """
    connection = connections.Connection(url, token)
    return connection.add_dataset(project=project, dataset=dataset, description=description, details=details, verbose=verbose)


@app.command()
def add_char_attribute(
    dataset:str,
    project:str,
    key:str,
    value:str,
    url:str = url_arg,
    token:str = token_arg,
    verbose:bool = True,
):
    """
    Adds a new char attribute to a dataset.
    """
    connection = connections.Connection(url, token)
    return connection.add_char_attribute(project=project, dataset=dataset, key=key, value=value, verbose=verbose)


@app.command()
def add_char_attribute(
    dataset:str,
    project:str,
    key:str,
    value:float,
    url:str = url_arg,
    token:str = token_arg,
    verbose:bool = True,
):
    """
    Adds a new float attribute to a dataset.
    """
    connection = connections.Connection(url, token)
    return connection.add_float_attribute(project=project, dataset=dataset, key=key, value=value, verbose=verbose)


@app.command()
def add_integer_attribute(
    dataset:str,
    project:str,
    key:str,
    value:int,
    url:str = url_arg,
    token:str = token_arg,
    verbose:bool = True,
):
    """
    Adds a new int attribute to a dataset.
    """
    connection = connections.Connection(url, token)
    return connection.add_integer_attribute(project=project, dataset=dataset, key=key, value=value, verbose=verbose)


@app.command()
def add_url_attribute(
    dataset:str,
    project:str,
    key:str,
    value:str,
    url:str = url_arg,
    token:str = token_arg,
    verbose:bool = True,
):
    """
    Adds a new int attribute to a dataset.
    """
    connection = connections.Connection(url, token)
    return connection.add_url_attribute(project=project, dataset=dataset, key=key, value=value, verbose=verbose)


@app.command()
def diagnostics():
    """ Display system diagnostics. """
    console.print( get_diagnostics() )




    