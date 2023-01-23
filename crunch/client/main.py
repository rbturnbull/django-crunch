from pathlib import Path
import typer
from rich.console import Console

console = Console()

from crunch.django.app import storages
from . import connections
from .diagnostics import get_diagnostics
from .enums import WorkflowType
from .run import Run


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
dataset_slug_arg = typer.Argument(..., help="The slug for the dataset.")
item_slug_arg = typer.Argument(..., help="The slug for the item.")
storage_settings_arg = typer.Option(
    ..., 
    envvar="CRUNCH_STORAGE_SETTINGS",
    help="The path to a JSON or TOML file with the Django settings for the storage.",
    prompt=True,
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
workflow_type_arg = typer.Option("snakemake", help="Workflow type (snakemake/script).")
path_arg = typer.Option(None, help="The path to the workflow file.")


@app.command()
def run(
    dataset: str = dataset_slug_arg,
    storage_settings: Path = storage_settings_arg,
    directory: Path = directory_arg,
    cores: str = cores_arg,
    url: str = url_arg,
    token: str = token_arg,
    workflow: WorkflowType = workflow_type_arg,
    path: Path = path_arg,
):
    """
    Processes a dataset.
    """
    r = Run(
        connection=connections.Connection(url, token), 
        dataset_slug=dataset, 
        working_directory=Path(directory),
        workflow_type=workflow, 
        storage_settings=storage_settings,
        workflow_path=path, 
        cores=cores,
    )

    r()


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
    workflow: WorkflowType = workflow_type_arg,
    path: Path = path_arg,
):
    """
    Processes the next dataset in a project.
    """
    console.print(f"Processing the next dataset from {url}")

    connection = connections.Connection(url, token)

    next_url = f"api/projects/{project}/next/" if project else "api/next/"
    next = connection.get_json_response(next_url)

    if "dataset" in next and "project" in next and next["project"] and next["dataset"]:
        run(
            dataset=next["dataset"],
            storage_settings=storage_settings,
            url=url,
            token=token,
            directory=directory,
            cores=cores,
            workflow=workflow,
            path=path,
        )
    else:
        console.print("No more datasets to process.")
        raise NoDatasets


@app.command()
def loop(
    storage_settings: Path = storage_settings_arg,
    directory: Path = directory_arg,
    cores: str = cores_arg,
    url: str = url_arg,
    token: str = token_arg,
    project: str = typer.Option(
        "",
        help="The slug for a project the dataset is in. If not given, then it chooses any project.",
    ),
    workflow: WorkflowType = workflow_type_arg,
    path: Path = path_arg,
):
    """
    Loops through all the datasets in a project and stops when complete.
    """
    console.print(
        f"Looping through all the datasets from {url} and will stop when complete."
    )
    while True:
        try:
            next(
                url=url,
                token=token,
                storage_settings=storage_settings,
                directory=directory,
                cores=cores,
                workflow=workflow,
                path=path,
                project=project,
            )
        except NoDatasets:
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


@app.command()
def files(
    dataset: str = dataset_slug_arg,
    storage_settings: Path = storage_settings_arg,
    url: str = url_arg,
    token: str = token_arg,
):
    """Displays the files for a dataset."""
    connection = connections.Connection(url, token)
    dataset_data = connection.get_json_response(f"/api/datasets/{dataset}/")
    base_file_path = dataset_data.get("base_file_path")

    storage = storages.get_storage_with_settings(storage_settings)
    listing = storages.storage_walk(base_file_path, storage=storage)
    console.print(listing.render())
