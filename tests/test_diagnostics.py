from unittest.mock import patch
import re
from django.test import TestCase
from crunch.client import diagnostics


def raise_oserror(*args, **kwargs):
    raise OSError


class DiagnosticsTestCase(TestCase):
    def test_git_revision(self):
        result = diagnostics.git_revision()
        assert re.match(r"\b[0-9a-f]{40}\b$", result)

    def test_get_diagnostics(self):
        result = diagnostics.get_diagnostics()
        assert isinstance(result, dict)
        assert "system_release" in result
        assert "disk_free" in result

    def test_version(self):
        result = diagnostics.version()
        assert re.match(r"^\d+\.\d+\.\d+$", result)

    def test_get_diagnostic_default(self):
        def raise_exception():
            raise Exception("error")

        d = dict()
        key = "key"
        default = "default"
        result = diagnostics.get_diagnostic(d, key, raise_exception, default=default)

        assert result == default
        assert d[key] == default

    @patch('subprocess.Popen', raise_oserror)
    def test_unknown(self):
        assert diagnostics.git_revision() == "Unknown"

