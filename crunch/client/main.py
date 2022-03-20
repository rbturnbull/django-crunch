import json
from pathlib import Path
from typing import Optional
from typing import List
from unicodedata import decimal
import typer
import subprocess
from rich.console import Console

console = Console()

from crunch.django.app import storages
from . import connections
from .diagnostics import get_diagnostics

from crunch.django.app.enums import Stage, State

class NoDatasets(Exception):
    """ Raised when there are no more datasets to process on a crunch site. """
    pass


app = typer.Typer()

url_arg = typer.Option(..., envvar="CRUNCH_URL", help="The URL for the endpoint for the project on the crunch hosted site.", prompt=True)
token_arg = typer.Option(..., envvar="CRUNCH_TOKEN", help="An access token for a user on the hosted site.", prompt=True)
project_slug_arg = typer.Argument(..., help="The slug for the project the dataset is in.")
dataset_slug_arg = typer.Argument(..., help="The slug for the dataset.")
item_slug_arg = typer.Argument(..., help="The slug for the item.")
storage_settings_arg = typer.Argument(..., help="The path to a JSON file with the Django settings for the storage.")
key_arg = typer.Argument(..., help="The key for this attribute.")
value_arg = typer.Argument(..., help="The value of this attribute.")
directory_arg = typer.Option("./tmp", help="The path to a directory to store the temporary files.")
cores_arg = typer.Option("1", help="The maximum number of cores/jobs to use to run the workflow. If 'all' then it uses all available cores.")


@app.command()
def run(
    project:str = project_slug_arg,
    dataset:str = dataset_slug_arg,
    storage_settings:Path = storage_settings_arg,
    directory:Path = directory_arg,
    cores:str = cores_arg,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Processes a dataset.
    """
    if not dataset:
        return

    console.print(f"Processing '{dataset}' from project '{project}' at {url}.")

    # Create temporary dir
    directory = Path(directory)
    directory.mkdir(exist_ok=True, parents=True)
    console.print(f"Using temporary directory '{directory}'.")

    # TODO Check to see if there is an old dataset.json
    connection = connections.Connection(url, token)

    # get dataset details
    dataset_data = connection.get_json_response( f"/api/datasets/{dataset}" )
    # TODO raise exception
    assert dataset_data['slug'] == dataset
    assert project in dataset_data['project']
    dataset_id = dataset_data['id']

    #############################
    ##       Setup Stage
    #############################
    stage = Stage.SETUP
    try:
        connection.send_status( dataset_id, stage=stage, state=State.START)
        with open(directory/'project.json', 'w', encoding='utf-8') as f:
            json.dump(dataset_data, f, ensure_ascii=False, indent=4)

        # get project details
        project_data = connection.get_json_response( f"/api/projects/{project}" )
        # TODO raise exception
        assert project_data['slug'] == project
        with open(directory/'project.json', 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=4)

        # Setup Storage
        if isinstance(storage_settings, Path):
            with open(storage_settings) as json_file:
                storage_settings = json.load(json_file)
        storage = storages.get_storage_with_settings(storage_settings)            

        # Pull data from storage
        storage_path = storages.dataset_path( project, dataset )        
        storages.copy_recursive_from_storage(storage_path, directory, storage=storage)

        # get snakefile
        with open(directory/'Snakefile', 'w', encoding='utf-8') as f:
            f.write(project_data['snakefile'])

        connection.send_status( dataset_id, stage=stage, state=State.SUCCESS)
    except Exception as e:
        connection.send_status( dataset_id, stage=stage, state=State.FAIL, note=str(e))

    #############################
    ##       Workflow Stage
    #############################

    stage = Stage.WORKFLOW
    try:
        connection.send_status( dataset_id, stage=stage, state=State.START)
        result = subprocess.Popen(["snakemake", "--cores", cores], cwd=directory)
        if result:
            raise Exception("Workflow failed")
        connection.send_status( dataset_id, stage=stage, state=State.SUCCESS)
    except Exception as e:
        connection.send_status( dataset_id, stage=stage, state=State.FAIL, note=str(e))

    #############################
    ##       Upload Stage
    #############################
    stage = Stage.UPLOAD

    # notify

    # print(result)
    return dataset_data


@app.command()
def next(
    storage_settings:Path = storage_settings_arg,
    directory:Path = directory_arg,
    cores:str = cores_arg,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Processes the next dataset in a project.
    """
    console.print(f"Processing the next dataset from {url}")
    connection = connections.Connection(url, token)
    next = connection.get_json_response( f"api/next/" )
    if 'dataset' in next and 'project' in next and next['project'] and next['dataset']:
        return run(
            project=next['project'], 
            dataset=next['dataset'], 
            storage_settings=storage_settings, 
            url=url, 
            token=token, 
            directory=directory, 
            cores=cores,
        )
    else:
        console.print("No more datasets to process.")


@app.command()
def loop(
    storage_settings:Path = storage_settings_arg,
    directory:Path = directory_arg,
    cores:str = cores_arg,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Loops through all the datasets in a project and stops when complete.
    """
    console.print(f"Looping through all the datasets from {url} and will stop when complete.")
    while True:
        result = next(url=url, token=token, storage_settings=storage_settings, directory=directory, cores=cores)
        if result is None:
            console.print("Loop concluded.")
            break


@app.command()
def add_project(
    project:str = typer.Argument(..., help="The name of the new crunch project."),
    description:str = typer.Option("", help="A brief description of this new project."),
    details:str = typer.Option("", help="A long description of this project in Markdown format."),
    verbose:bool = True,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new project on the hosted site.
    """
    connection = connections.Connection(url, token)
    return connection.add_project(project=project, description=description, details=details, verbose=verbose)


@app.command()
def add_dataset(
    project:str = typer.Argument(..., help="The slug of the project that this dataset is to be added to."),
    dataset:str = typer.Argument(..., help="The name of the new dataset"),
    description:str = typer.Option("", help="A brief description of this new dataset."),
    details:str = typer.Option("", help="A long description of this dataset in Markdown format."),
    verbose:bool = True,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new dataset to a project on the hosted site.
    """
    connection = connections.Connection(url, token)
    return connection.add_dataset(project=project, dataset=dataset, description=description, details=details, verbose=verbose)


@app.command()
def add_item(
    parent:str = typer.Argument(..., help="The slug of the item that this item is to be added to."),
    item:str = typer.Argument(..., help="The name of the new item"),
    description:str = typer.Option("", help="A brief description of this new item."),
    details:str = typer.Option("", help="A long description of this item in Markdown format."),
    verbose:bool = True,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new item to an item on the hosted site.
    """
    connection = connections.Connection(url, token)
    return connection.add_item(parent=parent, item=item, description=description, details=details, verbose=verbose)


@app.command()
def add_char_attribute(
    item:str = item_slug_arg,
    key:str = key_arg,
    value:str = value_arg,
    verbose:bool = True,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new char attribute to a dataset.
    """
    connection = connections.Connection(url, token)
    return connection.add_char_attribute(item=item, key=key, value=value, verbose=verbose)


@app.command()
def add_float_attribute(
    item:str = item_slug_arg,
    key:str = key_arg,
    value:float = value_arg,
    verbose:bool = True,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new float attribute to a dataset.
    """
    connection = connections.Connection(url, token)
    return connection.add_float_attribute(item=item, key=key, value=value, verbose=verbose)


@app.command()
def add_datetime_attribute(
    item:str = item_slug_arg,
    key:str = key_arg,
    value:str = value_arg,
    format:str="",
    verbose:bool = True,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new datetime attribute to a dataset.
    """
    connection = connections.Connection(url, token)
    return connection.add_datetime_attribute(item=item, key=key, value=value, format=format, verbose=verbose)


@app.command()
def add_date_attribute(
    item:str = item_slug_arg,
    key:str = key_arg,
    value:str = value_arg,
    format:str="",
    verbose:bool = True,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new date attribute to a dataset.
    """
    connection = connections.Connection(url, token)
    return connection.add_date_attribute(item=item, key=key, value=value, format=format, verbose=verbose)


@app.command()
def add_lat_long_attribute(
    item:str = item_slug_arg,
    key:str = key_arg,
    latitude:str = typer.Argument(..., help="The latitude of the coordinate in decimal degrees."),
    longitude:str = typer.Argument(..., help="The longitude of the coordinate in decimal degrees."),
    verbose:bool = True,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new lat-long coorinate as an attribute to a dataset.
    """
    connection = connections.Connection(url, token)
    return connection.add_lat_long_attribute(item=item, key=key, latitude=latitude, longitude=longitude, verbose=verbose)


@app.command()
def add_integer_attribute(
    item:str = item_slug_arg,
    key:str = key_arg,
    value:int = value_arg,
    verbose:bool = True,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new integer attribute to a dataset.
    """
    connection = connections.Connection(url, token)
    return connection.add_integer_attribute(item=item, key=key, value=value, verbose=verbose)


@app.command()
def add_boolean_attribute(
    item:str = item_slug_arg,
    key:str = key_arg,
    value:bool = value_arg,
    verbose:bool = True,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new boolean attribute to a dataset.
    """
    connection = connections.Connection(url, token)
    return connection.add_boolean_attribute(item=item, key=key, value=value, verbose=verbose)


@app.command()
def add_url_attribute(
    item:str = item_slug_arg,
    key:str = key_arg,
    value:str = value_arg,
    verbose:bool = True,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Adds a new URL attribute to a dataset.
    """
    connection = connections.Connection(url, token)
    return connection.add_url_attribute(item=item, key=key, value=value, verbose=verbose)


@app.command()
def diagnostics():
    """ Display system diagnostics. """
    console.print( get_diagnostics() )

