import pytest
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
from django.core.files.storage import FileSystemStorage

from crunch.django.app import storages

class MockSettings():
    def __init__(self, configured:bool=False):
        self.configured = configured
        self.config = None
        self.configure_called_count = 0
    
    def configure(self, **config):
        self.config = config
        self.configure_called_count += 1


TEST_DIR = Path(__file__).parent/"test-data"


def test_storage_directory_children():
    child1 = storages.StorageDirectory(base_path="/parent/child1")
    child2 = storages.StorageDirectory(base_path="/parent/child2")

    parent = storages.StorageDirectory(base_path="/parent", children=[child1, child2])
    assert parent.children[0] == child1
    assert parent.children[1] == child2
    parent.children[0].parent == parent
    parent.children[1].parent == parent


def test_render_html_error():
    class ExceptionStorageDirectory(storages.StorageDirectory):
        def short_str(self):
            raise ValueError # force an error
            
    child1 = storages.StorageDirectory(base_path="/parent/child1")
    child2 = ExceptionStorageDirectory(base_path="/parent/child2")
    parent = storages.StorageDirectory(base_path="/parent", children=[child1, child2])
    html = parent.render_html()
    assert html == "<div>Failed to read storage at /parent</div>"


def test_get_storage_with_settings_toml():
    mock_settings = MockSettings()
    with patch('crunch.django.app.storages.settings', mock_settings):
        storages.get_storage_with_settings(TEST_DIR/"settings.toml")
        assert mock_settings.configure_called_count == 1
        assert mock_settings.config == {"file_format":"toml"}


def test_get_storage_with_settings_json():
    mock_settings = MockSettings()
    with patch('crunch.django.app.storages.settings', mock_settings):
        storages.get_storage_with_settings(TEST_DIR/"settings.json")
        assert mock_settings.configure_called_count == 1
        assert mock_settings.config == {"file_format":"json"}        


def test_get_storage_with_settings_unknown_extension():
    mock_settings = MockSettings()
    with patch('crunch.django.app.storages.settings', mock_settings):
        with pytest.raises(IOError, match=r"Cannot find interpreter for"):
            storages.get_storage_with_settings(TEST_DIR/"dummy-files/dummy-file1.txt")


def test_get_storage_with_settings_unknown_object():
    mock_settings = MockSettings()
    with patch('crunch.django.app.storages.settings', mock_settings):
        with pytest.raises(ValueError, match=r"Please pass a dictionary or a path to a toml or json file"):
            storages.get_storage_with_settings(1)


def test_storage_walk():
    absolute_path = str(TEST_DIR.absolute())
    storage = FileSystemStorage(location=absolute_path, base_url="http://www.example.com")
    
    with patch('crunch.django.app.storages.default_storage', storage):
        root_dir = storages.storage_walk(base_path=absolute_path)
        assert isinstance(root_dir, storages.StorageDirectory)
        assert str(root_dir) == absolute_path
        assert root_dir.__repr__() == absolute_path
        assert root_dir.short_str() == ""

        subdirs = list(root_dir.directory_descendents())
        assert set([x.short_str() for x in subdirs]) == set(["", "dummy-files", "dummy-files2"])

        files = list(root_dir.file_descendents())
        expected = ['dummy-file1.txt', 'dummy-file2.txt', 'dummy-file3.txt', 'dummy-workflow-fail', 'settings.json', 'dummy-workflow', 'settings.toml']
        assert set([x.short_str() for x in files]) == set(expected)

        for file in files:
            if "dummy-file1.txt" == file.short_str():
                assert file.path() == TEST_DIR.absolute()/"dummy-files/dummy-file1.txt"
                assert file.__repr__() == "dummy-file1.txt"
                assert file.url() == f"http://www.example.com{file.path()}"

        immediate_files = root_dir.files()
        assert set([x.short_str() for x in immediate_files]) == set(['settings.json', 'settings.toml', 'dummy-workflow-fail', 'dummy-workflow', ])

        rendered = root_dir.render()
        assert 'django-crunch/tests/test-data\n' in rendered
        assert '── dummy-files\n' in rendered
        assert '── dummy-file1.txt\n' in rendered
        assert '── dummy-file2.txt\n' in rendered
        assert '── dummy-files2\n' in rendered
        assert '── dummy-file3.txt\n' in rendered
        assert '── settings.json\n' in rendered
        assert '── settings.toml\n' in rendered

        html = root_dir.render_html()
        assert "tests/test-data/dummy-files/dummy-file1.txt'>dummy-file1.txt</a>" in html
        assert "tests/test-data/settings.toml'>settings.toml</a>" in html


def test_storage_walk_with_dot():
    absolute_path = str(TEST_DIR.absolute())

    class FileSystemStorageWithDot(FileSystemStorage):
        def listdir(self, path:str):
            folders, filenames = super().listdir(path)
            folders.append(".")
            return folders, filenames

    storage = FileSystemStorageWithDot(location=absolute_path, base_url="http://www.example.com")
    
    with patch('crunch.django.app.storages.default_storage', storage):
        root_dir = storages.storage_walk(base_path=absolute_path)
        assert isinstance(root_dir, storages.StorageDirectory)
        assert str(root_dir) == absolute_path
        assert root_dir.__repr__() == absolute_path
        assert root_dir.short_str() == ""

        subdirs = list(root_dir.directory_descendents())
        assert sorted([x.short_str() for x in subdirs]) == sorted(["", "dummy-files", "dummy-files2"])

        files = list(root_dir.file_descendents())
        expected = ['dummy-file1.txt', 'dummy-file2.txt', 'dummy-file3.txt', 'dummy-workflow-fail', 'settings.json', 'dummy-workflow', 'settings.toml']
        assert set([x.short_str() for x in files]) == set(expected)

        for file in files:
            if "dummy-file1.txt" == file.short_str():
                assert file.path() == TEST_DIR.absolute()/"dummy-files/dummy-file1.txt"
                assert file.__repr__() == "dummy-file1.txt"
                assert file.url() == f"http://www.example.com{file.path()}"

        immediate_files = root_dir.files()
        assert set([x.short_str() for x in immediate_files]) == set(['settings.json', 'settings.toml', 'dummy-workflow-fail', 'dummy-workflow', ])

        rendered = root_dir.render()
        assert 'django-crunch/tests/test-data\n' in rendered
        assert '── dummy-files\n' in rendered
        assert '── dummy-file1.txt\n' in rendered
        assert '── dummy-file2.txt\n' in rendered
        assert '── dummy-files2\n' in rendered
        assert '── dummy-file3.txt\n' in rendered
        assert '── settings.json\n' in rendered
        assert '── settings.toml\n' in rendered

        html = root_dir.render_html()
        assert "tests/test-data/dummy-files/dummy-file1.txt'>dummy-file1.txt</a>" in html
        assert "tests/test-data/settings.toml'>settings.toml</a>" in html


def assert_test_data(directory:Path):
    os.path.getsize(directory/"settings.toml") > 0
    os.path.getsize(directory/"settings.json") > 0
    os.path.getsize(directory/"dummy-files/dummy-file1.txt") > 0
    os.path.getsize(directory/"dummy-files/dummy-file2.txt") > 0
    os.path.getsize(directory/"dummy-files2/dummy-file3.txt") > 0


def test_copy_recursive_from_storage():
    absolute_path = str(TEST_DIR.absolute())
    storage = FileSystemStorage(location=absolute_path, base_url="http://www.example.com")
    
    with patch('crunch.django.app.storages.default_storage', storage):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            storages.copy_recursive_from_storage(absolute_path, tmpdir)

            assert_test_data(tmpdir)


def test_copy_recursive_to_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        storage = FileSystemStorage(location=str(tmpdir), base_url="http://www.example.com")

        with patch('crunch.django.app.storages.default_storage', storage):
            storages.copy_recursive_to_storage(TEST_DIR, "./")

            assert_test_data(tmpdir)

