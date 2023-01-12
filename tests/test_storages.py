from pathlib import Path
from unittest.mock import patch

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