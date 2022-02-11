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
    console.print(f"Processing '{dataset}' from project '{project}' at {url}.")

    # Notify site to lock
    # setup stage

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

    # run workflow
    result = subprocess.Popen(["snakemake", "--cores", cores], cwd=directory)
    console.log(f"{result}")

    # push data 

    # notify

    # print(result)


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
    next = connections.get_json_response( url, f"/api/next/", token )
    if 'dataset' in next and 'project' in next:
        return run(project=next['project'], dataset=next['dataset'], url=url, token=token, directory=directory, cores=cores)


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
        next(url=url, token=token, directory=directory, cores=cores)


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
):
    """
    Adds a new dataset to a project on the hosted site.
    """
    console.print(f"Adding dataset '{dataset}' to project '{project}' on the hosted site {url}.")


@app.command()
def add_dataset(
    dataset:str,
    project:str,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new attribute to a dataset.
    """
    console.print(f"Adding attribute to dataset '{dataset}' to project '{project}' on the hosted site {url}.")

@app.command()
def diagnostics():
    """ Display system diagnostics. """
    console.print( get_diagnostics() )




    