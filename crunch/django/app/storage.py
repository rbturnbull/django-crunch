import logging 
from pathlib import Path


def django_storage_walk(base="/", storage=None, error_handler=None):
    """
    Recursively walks a folder, using Django's File Storage.
    :param base: <str> The base folder
    :param storage: <Storage>
    :param error_handler: <callable>
    :yields: A tuple of basedir, subfolders, files
    
    Adapted from https://gist.github.com/dvf/c103e697dab77c304d39d60cf279c500
    """
    if storage is None:
        from django.core.files.storage import default_storage
        storage = default_storage

    try:
        folders, files = storage.listdir(str(base))
    except OSError as e:
        logging.exception("An error occurred while walking directory %s", base)
        if error_handler:
            error_handler(e)
        return

    for subfolder in folders:
        # On S3, we don't have subfolders, so exclude "."
        if subfolder == ".":
            continue

        new_base = Path(base, subfolder)
        for f in django_storage_walk(base=new_base, storage=storage, error_handler=error_handler):
            yield f

    yield str(base), folders, files
