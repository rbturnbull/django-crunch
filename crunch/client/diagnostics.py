import platform, socket, re, uuid, psutil, os
import getpass

import os
from pathlib import Path
import subprocess

def version() -> str:
    """
    Gets the version number of the django-crunch module.

    Returns:
        str: The current version.
    """
    import importlib.metadata
    version = importlib.metadata.version("django-crunch")
    return version


# Return the git revision as a string
def git_revision(directory:Path=None) -> str:
    """
    Gets the git revision hash for a directory.

    Adapted from https://stackoverflow.com/a/40170206 which was taken from NumPy.

    Args:
        directory (Path, optional): The directory we are interested in. Defaults to None in which case it uses the directory of the current source file.

    Returns:
        str: The git hash for the current revision.
    """
    directory = directory or Path(__file__).parent
    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {}
        for k in ['SYSTEMROOT', 'PATH']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
        # LANGUAGE is used on win32
        env['LANGUAGE'] = 'C'
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
        out = subprocess.Popen(cmd, stdout = subprocess.PIPE, env=env, cwd=directory).communicate()[0]
        return out

    try:
        out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
        GIT_REVISION = out.strip().decode('ascii')
    except OSError:
        GIT_REVISION = "Unknown"

    return GIT_REVISION

def get_diagnostic(diagnostics:dict, key:str, func, default=""):
    try:
        result = func()
    except Exception:
        result = default
    diagnostics[key] = result
    return result

def get_diagnostics() -> dict:
    """
    Gets diagnostic information about the current environment.

    Used when sending status updates to a crunch hosted site.

    Returns:
        dict: A dictionary with the diagnostic information.
    """
    diagnostics = dict()

    # adapts code from here: https://stackoverflow.com/questions/3103178/how-to-get-the-system-info-with-python
    get_diagnostic(diagnostics, 'agent_user', lambda: getpass.getuser())
    get_diagnostic(diagnostics, 'version', lambda: version())
    get_diagnostic(diagnostics, 'revision', lambda: git_revision())
    get_diagnostic(diagnostics, 'system', lambda: platform.system())
    get_diagnostic(diagnostics, 'system_release', lambda: platform.release())
    get_diagnostic(diagnostics, 'system_version', lambda: platform.version())
    get_diagnostic(diagnostics, 'machine', lambda: platform.machine())
    get_diagnostic(diagnostics, 'hostname', lambda: socket.gethostname())
    get_diagnostic(diagnostics, 'ip_address', lambda: socket.gethostbyname(socket.gethostname())) # this could use the hostname from above
    get_diagnostic(diagnostics, 'mac_address', lambda: ':'.join(re.findall('..', '%012x' % uuid.getnode())))
    get_diagnostic(diagnostics, 'memory_total', lambda: psutil.virtual_memory().total, default=None)
    get_diagnostic(diagnostics, 'memory_free', lambda: psutil.virtual_memory().available, default=None)
    get_diagnostic(diagnostics, 'disk_total', lambda: psutil.disk_usage(os.getcwd()).total, default=None)
    get_diagnostic(diagnostics, 'disk_free', lambda: psutil.disk_usage(os.getcwd()).free, default=None)

    return diagnostics