import stat
import subprocess
from pathlib import Path
import hashlib

from .enums import WorkflowType


def has_mamba()->bool:
    """
    Checks to see if mamba is available.

    Returns:
        bool: Whether or not mamba is in the path.
    """
    try:
        subprocess.run(["mamba", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

    return True


def conda_frontend() -> str:
    return "mamba" if has_mamba() else "conda"


def write_workflow(data:str, working_directory:Path, workflow_type:WorkflowType) -> Path:
    assert data
    working_directory = Path(working_directory)
    working_directory.mkdir(exist_ok=True, parents=True)
    
    if workflow_type == WorkflowType.snakemake:
        workflow_path = working_directory / "Snakefile"
    elif workflow_type == WorkflowType.script:
        workflow_path = working_directory / "script.sh"
    
    with open(workflow_path, "w", encoding="utf-8") as f:
        f.write(data.replace('\r\n', '\n'))

    if workflow_type == WorkflowType.script:
        workflow_path.chmod(workflow_path.stat().st_mode | stat.S_IEXEC)

    return workflow_path


def md5_checksums(directory):
    directory = Path(directory)
    result = dict()
    for path in directory.rglob("*"):
        if path.is_dir():
            continue
        
        relative_path = path.relative_to(directory)
        md5 = hashlib.md5(path.read_bytes()).hexdigest()
        result[str(relative_path)] = md5

    return result
