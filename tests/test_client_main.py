from typer.testing import CliRunner
from django.test import TestCase
from crunch.client.main import app

runner = CliRunner()


class ClientMainTestCase(TestCase):
    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Usage: " in result.stdout
