import os 
import tempfile
from unittest.mock import patch
import subprocess

from crunch.client import utils, enums

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
        path = utils.write_workflow("test", tmpdir, enums.WorkflowType.script)
        assert path.name == "script.sh"
        assert str(path.parent) == str(tmpdir)
        assert os.access(path, os.X_OK)


def test_write_workflow_snakemake():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = utils.write_workflow("test", tmpdir, enums.WorkflowType.snakemake)
        assert path.name == "Snakefile"
        assert str(path.parent) == str(tmpdir)

