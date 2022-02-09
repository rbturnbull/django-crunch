import os
import sys
from pathlib import Path
from typing import Optional
from typing import List
import typer

app = typer.Typer()

url_arg = typer.Argument(..., envvar="CRUNCH_URL", help="The URL for the endpoint for the project on the hosted site.")
token_arg = typer.Argument(..., envvar="CRUNCH_TOKEN", help="An access token for a user on the hosted site.")

@app.command()
def run(
    dataset:str,
    url:str = url_arg,
    token:str = token_arg,
):
    """
    Processes a dataset.
    """
    print(f"Processing {dataset} from {url}")


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


def django_command(command, args=None):
    # Path(__file__).parent.parent.resolve()/"django/proj"/settings"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crunch.django.proj.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django  # noqa
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )

        raise

    if args is None:
        args = []

    execute_from_command_line(["./manage.py"] + [command] + args)



@app.command()
def runserver():
    return django_command("runserver")


@app.command()
def migrate():
    return django_command("migrate")


@app.command()
def createsuperuser():
    return django_command("createsuperuser")    