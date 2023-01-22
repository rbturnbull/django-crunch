import logging
from typing import Dict, Union
import toml
import json
from operator import mod
from pathlib import Path
from django.core.files import File
from django.conf import settings
from anytree import NodeMixin, RenderTree, PreOrderIter
from django.core.files.storage import default_storage, DefaultStorage
import os
import time
import shutil
import datetime


class Directory:
    pass


def get_storage_with_settings(storage_settings:Union[Dict,Path]) -> DefaultStorage:
    """
    Configures the Django config with settings if it has not been configured yet and then returns the default storage.

    Useful for connecting to a Django storage object outside of a webserver.

    Args:
        storage_settings (Union[Dict,Path]): The settings with which to configure the Django config if it has not been configured already.
            Can be a dictionary with settings or can be a path to a toml or json file with the settings.

    Raises:
        IOError: Raised if passed a Path object which isn't a toml or json file.
        ValueError: Raised if the settings cannot be interpreted as a dictionary.

    Returns:
        DefaultStorage: The default storage object used by Django.
    """
    if not settings.configured:
        if isinstance(storage_settings, Path):
            with open(storage_settings) as storage_settings_file:
                suffix = storage_settings.suffix.lower()
                if suffix == ".toml":
                    storage_settings = toml.load(storage_settings_file)
                elif suffix == ".json":
                    storage_settings = json.load(storage_settings_file)
                else:
                    raise IOError(f"Cannot find interpreter for {storage_settings}")

        if not isinstance(storage_settings, dict):
            raise ValueError(
                f"Storage settings of type {type(storage_settings)} unable to be read. " +
                "Please pass a dictionary or a path to a toml or json file."
            )
        settings.configure(**storage_settings)
    return default_storage


class StorageDirectory(NodeMixin):
    def __init__(
        self, *args, base_path: Union[str,Path], storage=None, parent=None, children=None, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.base_path = Path(base_path)
        self.storage = storage
        self.parent = parent
        if children:
            self.children = children

    def __str__(self):
        return str(self.base_path)

    def __repr__(self):
        return str(self)

    def files(self):
        """Returns a list of StorageFile objects for files in this immediate directory."""
        return [child for child in self.children if isinstance(child, StorageFile)]

    def short_str(self):
        if self.parent:
            return str(self.base_path.relative_to(self.parent.base_path))
        return ""

    def render(self):
        result = f"{self.base_path}\n"
        for pre, _, node in RenderTree(self):
            if node == self:
                continue
            treestr = f"{pre}{node.short_str()}"
            result += treestr.ljust(8) + "\n"
        return result

    def render_html(self):
        try:
            result = "<div>"
            result += f"{self.base_path}<br>\n"
            for pre, _, node in RenderTree(self):
                if node == self:
                    continue

                if isinstance(node, StorageFile):
                    result += f"{pre}<a href='{node.url()}'>{node.short_str()}</a><br>\n"
                else:
                    result += f"{pre}{node.short_str()}<br>\n"
            result += "</div>"
        except Exception as err:
            result = f"<div>Failed to read storage at {self.base_path}</div>"
            
        return result

    def directory_descendents(self, stop=None, maxlevel: int = None):
        """Does a pre order iteration of subdirectories."""
        return PreOrderIter(
            self,
            filter_=lambda node: isinstance(node, StorageDirectory),
            stop=stop,
            maxlevel=maxlevel,
        )

    def file_descendents(self, stop=None, maxlevel: int = None):
        """Does a pre order iteration of subdirectories and returns the files in them."""
        return PreOrderIter(
            self,
            filter_=lambda node: isinstance(node, StorageFile),
            stop=stop,
            maxlevel=maxlevel,
        )


class StorageFile(NodeMixin):
    def __init__(self, *args, filename, parent, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = filename
        self.parent = parent

    def __str__(self):
        return self.filename

    def short_str(self):
        return str(self)

    def __repr__(self):
        return str(self)

    def path(self) -> Path:
        return Path(self.parent.base_path, self.filename)

    def url(self):
        storage = self.parent.storage or default_storage
        return storage.url(str(self.path()))


def storage_walk(
    base_path="/", storage=None, parent=None
) -> StorageDirectory:
    """
    Recursively walks a folder, using Django's File Storage.

    Adapted from https://gist.github.com/dvf/c103e697dab77c304d39d60cf279c500
    """
    if storage is None:
        storage = default_storage

    folders, filenames = storage.listdir(str(base_path))

    directory = StorageDirectory(base_path=base_path, parent=parent, storage=storage)

    for subfolder in folders:
        # On S3, we don't have subfolders, so exclude "."
        if subfolder == ".":
            continue

        new_base = Path(base_path, subfolder)
        storage_walk(
            base_path=new_base,
            storage=storage,
            parent=directory,
        )

    for filename in filenames:
        StorageFile(filename=filename, parent=directory)

    return directory


def default_dataset_path(project_slug, dataset_slug):
    return Path("crunch", project_slug, dataset_slug)


def copy_recursive_to_storage(local_dir=".", base="/", storage=None):    
    copy_to_storage(local_dir.rglob("*"), local_dir=local_dir, base=base, storage=storage)


def copy_to_storage(paths, local_dir, base="/", storage=None):
    base = Path(base)
    if storage is None:
        storage = default_storage

    for local_path in paths:
        if local_path.is_dir():
            continue

        local_relative_path = local_path.relative_to(local_dir)
        remote_path = str(base / local_relative_path)

        print(
            f"Copying '{local_path}' from local directory '{local_dir}' to storage at '{remote_path}'"
        )
        with local_path.open(mode="rb") as f:
            storage._save(remote_path, File(f, name=str(local_path)))  


def copy_recursive_from_storage(base="/", local_dir=".", storage=None):
    base = Path(base)
    local_dir = Path(local_dir)
    if storage is None:
        storage = default_storage

    dir_object = storage_walk(base_path=base, storage=storage)
    subdirs = dir_object.directory_descendents()

    for subdir in subdirs:
        listing_path = Path(subdir.base_path)
        relative_path = listing_path.relative_to(base)
        local_path = local_dir / relative_path
        local_path.mkdir(exist_ok=True, parents=True)

        for file in subdir.files():
            filename = file.filename
            print(
                f"Copying '{filename}' in '{listing_path}' from storage to '{local_path}'"
            )
            with storage.open(str(listing_path / filename), "rb") as source:
                with open(local_path / filename, "wb") as target:
                    shutil.copyfileobj(source, target, length=1024)
