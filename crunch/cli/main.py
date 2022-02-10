import os
import sys
from pathlib import Path
from typing import Optional
from typing import List
import typer

from . import connections

app = typer.Typer()

url_arg = typer.Argument(..., envvar="CRUNCH_URL", help="The URL for the endpoint for the project on the hosted site.")
token_arg = typer.Argument(..., envvar="CRUNCH_TOKEN", help="An access token for a user on the hosted site.")

@app.command()
def run(
    project:str,
    dataset:str,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Processes a dataset.
    """
    print(f"Processing {dataset} from project {project} at {url}.")
    result = connections.get_json_response( url, f"/api/datasets/{dataset}", token )
    print(result)


@app.command()
def next(
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Processes the next dataset in a project.
    """
    print(f"Processing the next dataset from {url}")


@app.command()
def loop(
    url:str = url_arg,
    token:str = token_arg,
    project:str = "",
):
    """
    Loops through all the datasets in a project and stops when complete.
    """
    print(f"Looping through all the datasets from {url} and will stop when complete.")




@app.command()
def add_project(
    name:str,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new project to the hosted site.
    """
    print(f"Adding project {name} on the hosted site {url}.")


@app.command()
def add_dataset(
    name:str,
    project:str,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new dataset to a project on the hosted site.
    """
    print(f"Adding dataset {name} to project {project} on the hosted site {url}.")



    