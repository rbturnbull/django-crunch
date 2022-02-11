import platform, socket, re, uuid, psutil, os
import getpass

def get_diagnostic(diagnostics, key, func, default=""):
    try:
        result = func()
    except Exception:
        result = default
    diagnostics[key] = result
    return result

def get_diagnostics():
    diagnostics = dict()

    # adapts code from here: https://stackoverflow.com/questions/3103178/how-to-get-the-system-info-with-python
    get_diagnostic(diagnostics, 'agent_user', lambda: getpass.getuser())
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