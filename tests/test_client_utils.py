import os 
import tempfile
from unittest.mock import patch
import subprocess

from crunch.client import utils, enums

from .test_storages import TEST_DIR


def raise_called_process_error(*args, **kwargs):
    raise subprocess.CalledProcessError(returncode=1, cmd=[])


@patch('subprocess.run', lambda *args, **kwargs: 0 )
def test_has_mamba():
    assert utils.has_mamba()


@patch("subprocess.run", raise_called_process_error )
def test_no_mamba():
    assert not utils.has_mamba()    


@patch('subprocess.run', lambda *args, **kwargs: 0 )
def test_conda_frontend_mamba():
    assert utils.conda_frontend() == "mamba"


@patch("subprocess.run", raise_called_process_error )
def test_conda_frontend():
    assert utils.conda_frontend() == "conda"


def test_write_workflow_script():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = utils.write_workflow("test", tmpdir)
        assert path.name == "script.sh"
        assert str(path.parent) == str(tmpdir)
        assert os.access(path, os.X_OK)


def test_write_workflow_snakemake():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = utils.write_workflow("test", tmpdir)
        assert path.name == "Snakefile"
        assert str(path.parent) == str(tmpdir)


def test_md5_checksums():
    md5_checksums = utils.md5_checksums(TEST_DIR)
    assert md5_checksums == {
        "settings.json":"6d6e1697f767219819915aa98b43f373",
        "settings.toml":"47bfe028dba88f4f04a72b9e60f0b54a",
        "dummy-files/dummy-file1.txt":"d35cf79ba12e01ed0f9b850263c3692d",
        "dummy-files/dummy-file2.txt":"3efe3d9bd803f9514e0eeb8033114efe",
        "dummy-files2/dummy-file3.txt":"e0fd2de670cc2b9e43b198a7ff5f952d",
        'dummy-workflow-fail': '8e7afad177af27fd5e93af0c199dc7c7',
        'dummy-workflow': 'e0f10798ad1df2b1032189ec5c7b62f6',
    }