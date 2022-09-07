import logging
from operator import mod 
from pathlib import Path
from django.core.files import File
from django.conf import settings
from django.core.files.storage import default_storage
import os
import time
import shutil
import datetime

class Directory:
    pass


def get_storage_with_settings(**settings_kwargs):
    if not settings.configured:
        settings.configure(**settings_kwargs)
    return default_storage


def storage_walk(base="/", storage=None, error_handler=None):
    """
    Recursively walks a folder, using Django's File Storage.

    :param base: <str> The base folder
    :param storage: <Storage>
    :param error_handler: <callable>
    :yields: A tuple of basedir, subfolders, files
    
    Adapted from https://gist.github.com/dvf/c103e697dab77c304d39d60cf279c500
    """
    if storage is None:
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
        for f in storage_walk(base=new_base, storage=storage, error_handler=error_handler):
            yield f

    yield str(base), folders, files


def dataset_path(project_slug, dataset_slug):
    return Path('crunch', project_slug, dataset_slug)


def copy_recursive_to_storage(local_dir=".", base="/", storage=None):
    base = Path(base)
    local_dir = Path(local_dir)
    if storage is None:
        storage = default_storage

    for local_path in local_dir.rglob("*"):
        if local_path.is_dir():
            continue

        local_relative_path = local_path.relative_to(local_dir)
        remote_path = str(base/local_relative_path)
        
        if str(local_relative_path).startswith(".snakemake/"):
            continue

        if storage.exists(remote_path):
            remote_mod_time = storage.get_modified_time(remote_path)
            local_mod_time = datetime.datetime.fromtimestamp(local_path.lstat().st_mtime)
            
            if remote_mod_time >= local_mod_time:
                continue

        print(f"Copying '{local_path}' from local directory '{local_dir}' to storage at '{remote_path}'")
        with local_path.open(mode='rb') as f:
            storage._save(remote_path, File(f, name=str(local_path)))


def copy_recursive_from_storage(base="/", local_dir=".", storage=None):
    base = Path(base)
    local_dir = Path(local_dir)
    if storage is None:
        storage = default_storage

    listings = storage_walk(base=base, storage=storage)

    for listing in listings:
        listing_path = Path(listing[0])
        relative_path = listing_path.relative_to(base)
        local_path = local_dir/relative_path
        local_path.mkdir(exist_ok=True, parents=True)

        filenames = listing[2]
        for filename in filenames:
            print(f"Copying '{filename}' in '{listing_path}' from storage to '{local_path}'")
            with storage.open(str(listing_path/filename),'rb') as source:
                with open(local_path/filename,'wb') as target:
                    shutil.copyfileobj(source, target, length=1024)
                
            # Set the modification time so it is the same as on the storage
            mod_time = storage.get_modified_time(str(listing_path/filename))
            print("mod_time", mod_time)
            utime = time.mktime(mod_time.timetuple())
            os.utime(str(local_path/filename), (utime,utime) )
