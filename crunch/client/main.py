import json
import toml
from pathlib import Path
from typing import Optional
import traceback
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
    """Raised when there are no more datasets to process on a crunch site."""

    pass


app = typer.Typer()

url_arg = typer.Option(
    ...,
    envvar="CRUNCH_URL",
    help="The URL for the endpoint for the project on the crunch hosted site.",
    prompt=True,
)
token_arg = typer.Option(
    ...,
    envvar="CRUNCH_TOKEN",
    help="An access token for a user on the hosted site.",
    prompt=True,
)
project_slug_arg = typer.Argument(
    ..., help="The slug for the project the dataset is in."
)
dataset_slug_arg = typer.Argument(..., help="The slug for the dataset.")
item_slug_arg = typer.Argument(..., help="The slug for the item.")
storage_settings_arg = typer.Argument(
    ..., help="The path to a JSON file with the Django settings for the storage."
)
key_arg = typer.Argument(..., help="The key for this attribute.")
value_arg = typer.Argument(..., help="The value of this attribute.")
directory_arg = typer.Option(
    "./tmp", help="The path to a directory to store the temporary files."
)
cores_arg = typer.Option(
    "1",
    help="The maximum number of cores/jobs to use to run the workflow. If 'all' then it uses all available cores.",
)
snakefile_arg = typer.Option(..., help="The path to the snakemake file.")


@app.command()
def run(
    project: str = project_slug_arg,
    dataset: str = dataset_slug_arg,
    storage_settings: Path = storage_settings_arg,
    directory: Path = directory_arg,
    cores: str = cores_arg,
    url: str = url_arg,
    token: str = token_arg,
    snakefile: Path = typer.Option(None, help="The path to the snakemake file."),
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
    dataset_data = connection.get_json_response(f"/api/datasets/{dataset}")
    # TODO raise exception
    assert dataset_data["slug"] == dataset
    assert project in dataset_data["parent"]
    dataset_id = dataset_data["id"]

    stage_style = "bold red"

    #############################
    ##       Setup Stage
    #############################
    console.print(f"Setup stage {dataset}", style=stage_style)
    stage = Stage.SETUP
    try:
        connection.send_status(dataset_id, stage=stage, state=State.START)
        with open(directory / "dataset.json", "w", encoding="utf-8") as f:
            json.dump(dataset_data, f, ensure_ascii=False, indent=4)

        # get project details
        project_data = connection.get_json_response(f"/api/projects/{project}")
        # TODO raise exception
        assert project_data["slug"] == project
        with open(directory / "project.json", "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=4)

        # Setup Storage
        if isinstance(storage_settings, Path):
            with open(storage_settings) as storage_settings_file:
                suffix = storage_settings.suffix.lower()
                if suffix == ".toml":
                    storage_settings = toml.load(storage_settings_file)
                elif suffix == ".json":
                    storage_settings = json.load(storage_settings_file)
                else:
                    raise Exception(f"Cannot find interpreter for {storage_settings}")

        storage = storages.get_storage_with_settings(**storage_settings)

        # Pull data from storage
        storages.copy_recursive_from_storage(
            dataset_data["base_file_path"], directory, storage=storage
        )

        # get snakefile
        if not snakefile:
            assert project_data["snakefile"]
            snakefile = directory / "Snakefile"
            with open(snakefile, "w", encoding="utf-8") as f:
                f.write(project_data["snakefile"])

        connection.send_status(dataset_id, stage=stage, state=State.SUCCESS)
    except Exception as e:
        console.print(f"Setup failed {dataset}: {e}", style=stage_style)
        connection.send_status(dataset_id, stage=stage, state=State.FAIL, note=str(e))
        return

    #############################
    ##       Workflow Stage
    #############################
    console.print(f"Workflow stage {dataset}", style=stage_style)
    stage = Stage.WORKFLOW

    try:
        connection.send_status(dataset_id, stage=stage, state=State.START)
        import snakemake

        args = [
            f"--snakefile={snakefile}",
            "--use-conda",
            f"--cores={cores}",
            f"--directory={directory}",
        ]
        mamba_found = True
        try:
            subprocess.run(["mamba", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            mamba_found = False
        if not mamba_found:
            args.append("--conda-frontend=conda")

        try:
            snakemake.main(args)
        except SystemExit as result:
            print(f"result {result}")

        connection.send_status(dataset_id, stage=stage, state=State.SUCCESS)
    except Exception as e:
        console.print(f"Workflow failed {dataset}: {e}", style=stage_style)
        connection.send_status(dataset_id, stage=stage, state=State.FAIL, note=str(e))

    #############################
    ##       Upload Stage
    #############################
    console.print(f"Upload stage {dataset}", style=stage_style)
    stage = Stage.UPLOAD
    try:
        connection.send_status(dataset_id, stage=stage, state=State.START)
        storages.copy_recursive_to_storage(
            directory, dataset_data["base_file_path"], storage=storage
        )
        connection.send_status(dataset_id, stage=stage, state=State.SUCCESS)
    except Exception as e:
        console.print(f"Upload failed {dataset}: {e}", style=stage_style)
        traceback.print_exc()
        connection.send_status(dataset_id, stage=stage, state=State.FAIL, note=str(e))

    return dataset_data


@app.command()
def next(
    storage_settings: Path = storage_settings_arg,
    directory: Path = directory_arg,
    cores: str = cores_arg,
    url: str = url_arg,
    token: str = token_arg,
    project: str = typer.Option(
        "",
        help="The slug for a project the dataset is in. If not given, then it chooses any project.",
    ),
    snakefile: Path = snakefile_arg,
):
    """
    Processes the next dataset in a project.
    """
    console.print(f"Processing the next dataset from {url}")

    connection = connections.Connection(url, token)

    next = (
        connection.get_json_response(f"api/projects/{project}/next/")
        if project
        else connection.get_json_response(f"api/next/")
    )

    if "dataset" in next and "project" in next and next["project"] and next["dataset"]:
        return run(
            project=next["project"],
            dataset=next["dataset"],
            storage_settings=storage_settings,
            url=url,
            token=token,
            directory=directory,
            cores=cores,
            snakefile=snakefile,
        )
    else:
        console.print("No more datasets to process.")


@app.command()
def loop(
    storage_settings: Path = storage_settings_arg,
    directory: Path = directory_arg,
    cores: str = cores_arg,
    url: str = url_arg,
    token: str = token_arg,
    snakefile: Path = snakefile_arg,
):
    """
    Loops through all the datasets in a project and stops when complete.
    """
    console.print(
        f"Looping through all the datasets from {url} and will stop when complete."
    )
    while True:
        result = next(
            url=url,
            token=token,
            storage_settings=storage_settings,
            directory=directory,
            cores=cores,
            snakefile=snakefile,
        )
        if result is None:
            console.print("Loop concluded.")
            break


@app.command()
def add_project(
    project: str = typer.Argument(..., help="The name of the new crunch project."),
    description: str = typer.Option(
        "", help="A brief description of this new project."
    ),
    details: str = typer.Option(
        "", help="A long description of this project in Markdown format."
    ),
    verbose: bool = True,
    url: str = url_arg,
    token: str = token_arg,
):
    """
    Adds a new project on the hosted site.
    """
    connection = connections.Connection(url, token, verbose=verbose)
    return connection.add_project(
        project=project, description=description, details=details
    )


@app.command()
def add_dataset(
    project: str = typer.Argument(
        ..., help="The slug of the project that this dataset is to be added to."
    ),
    dataset: str = typer.Argument(..., help="The name of the new dataset"),
    description: str = typer.Option(
        "", help="A brief description of this new dataset."
    ),
    details: str = typer.Option(
        "", help="A long description of this dataset in Markdown format."
    ),
    verbose: bool = True,
    url: str = url_arg,
    token: str = token_arg,
):
    """
    Adds a new dataset to a project on the hosted site.
    """
    connection = connections.Connection(url, token, verbose=verbose)
    return connection.add_dataset(
        project=project, dataset=dataset, description=description, details=details
    )


@app.command()
def add_item(
    parent: str = typer.Argument(
        ..., help="The slug of the item that this item is to be added to."
    ),
    item: str = typer.Argument(..., help="The name of the new item"),
    description: str = typer.Option("", help="A brief description of this new item."),
    details: str = typer.Option(
        "", help="A long description of this item in Markdown format."
    ),
    verbose: bool = True,
    url: str = url_arg,
    token: str = token_arg,
):
    """
    Adds a new item to an item on the hosted site.
    """
    connection = connections.Connection(url, token, verbose=verbose)
    return connection.add_item(
        parent=parent, item=item, description=description, details=details
    )


@app.command()
def add_char_attribute(
    item: str = item_slug_arg,
    key: str = key_arg,
    value: str = value_arg,
    verbose: bool = True,
    url: str = url_arg,
    token: str = token_arg,
):
    """
    Adds a new char attribute to an item.
    """
    connection = connections.Connection(url, token, verbose=verbose)
    return connection.add_char_attribute(item=item, key=key, value=value)


@app.command()
def add_float_attribute(
    item: str = item_slug_arg,
    key: str = key_arg,
    value: float = value_arg,
    verbose: bool = True,
    url: str = url_arg,
    token: str = token_arg,
):
    """
    Adds a new float attribute to an item.
    """
    connection = connections.Connection(url, token, verbose=verbose)
    return connection.add_float_attribute(item=item, key=key, value=value)


@app.command()
def add_datetime_attribute(
    item: str = item_slug_arg,
    key: str = key_arg,
    value: str = value_arg,
    format: str = "",
    verbose: bool = True,
    url: str = url_arg,
    token: str = token_arg,
):
    """
    Adds a new datetime attribute to an item.
    """
    connection = connections.Connection(url, token, verbose=verbose)
    return connection.add_datetime_attribute(
        item=item, key=key, value=value, format=format
    )


@app.command()
def add_date_attribute(
    item: str = item_slug_arg,
    key: str = key_arg,
    value: str = value_arg,
    format: str = "",
    verbose: bool = True,
    url: str = url_arg,
    token: str = token_arg,
):
    """
    Adds a new date attribute to an item.
    """
    connection = connections.Connection(url, token, verbose=verbose)
    return connection.add_date_attribute(item=item, key=key, value=value, format=format)


@app.command()
def add_lat_long_attribute(
    item: str = item_slug_arg,
    key: str = key_arg,
    latitude: str = typer.Argument(
        ..., help="The latitude of the coordinate in decimal degrees."
    ),
    longitude: str = typer.Argument(
        ..., help="The longitude of the coordinate in decimal degrees."
    ),
    verbose: bool = True,
    url: str = url_arg,
    token: str = token_arg,
):
    """
    Adds a new lat-long coorinate as an attribute to an item.
    """
    connection = connections.Connection(url, token, verbose=verbose)
    return connection.add_lat_long_attribute(
        item=item, key=key, latitude=latitude, longitude=longitude
    )


@app.command()
def add_integer_attribute(
    item: str = item_slug_arg,
    key: str = key_arg,
    value: int = value_arg,
    verbose: bool = True,
    url: str = url_arg,
    token: str = token_arg,
):
    """
    Adds a new integer attribute to an item.
    """
    connection = connections.Connection(url, token, verbose=verbose)
    return connection.add_integer_attribute(item=item, key=key, value=value)


@app.command()
def add_filesize_attribute(
    item: str = item_slug_arg,
    key: str = key_arg,
    value: int = value_arg,
    verbose: bool = True,
    url: str = url_arg,
    token: str = token_arg,
):
    """
    Adds a new filesize attribute to an item.
    """
    connection = connections.Connection(url, token, verbose=verbose)
    return connection.add_filesize_attribute(item=item, key=key, value=value)


@app.command()
def add_boolean_attribute(
    item: str = item_slug_arg,
    key: str = key_arg,
    value: bool = value_arg,
    verbose: bool = True,
    url: str = url_arg,
    token: str = token_arg,
):
    """
    Adds a new boolean attribute to an item.
    """
    connection = connections.Connection(url, token, verbose=verbose)
    return connection.add_boolean_attribute(item=item, key=key, value=value)


@app.command()
def add_url_attribute(
    item: str = item_slug_arg,
    key: str = key_arg,
    value: str = value_arg,
    verbose: bool = True,
    url: str = url_arg,
    token: str = token_arg,
):
    """
    Adds a new URL attribute to an item.
    """
    connection = connections.Connection(url, token, verbose=verbose)
    return connection.add_url_attribute(item=item, key=key, value=value)


@app.command()
def diagnostics():
    """Display system diagnostics."""
    console.print(get_diagnostics())
