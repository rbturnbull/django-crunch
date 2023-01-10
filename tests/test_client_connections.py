import pytest
from unittest.mock import patch
from crunch.client import connections
from crunch.django.app.enums import Stage, State

class MockResponse():
    def __init__(self, data=None, status_code=200, reason=""):
        self.data = data
        self.status_code = status_code
        self.reason = reason

    def json(self):
        return self.data


@patch('requests.get', lambda *args, **kwargs: MockResponse(data={"detail": "Not found"}))
def test_get_json_response_error():
    connection = connections.Connection(base_url="http://www.example.com", token="token")

    with pytest.raises(connections.CrunchAPIException, match=r"Error getting JSON response from URL 'http://www.example.com/test':"):
        connection.get_json_response("test")


@patch('requests.get', lambda *args, **kwargs: MockResponse(data={"id": "1", "name":"Test Project"}))
def test_get_json_response():
    connection = connections.Connection(base_url="http://www.example.com", token="token")
    result = connection.get_json_response("test")
    assert len(result.keys()) == 2
    assert result['id'] == "1"
    assert result['name'] == "Test Project"


@patch('requests.post', lambda *args, **kwargs: MockResponse(status_code=200))
def test_post():
    connection = connections.Connection(base_url="http://www.example.com", token="token")
    result = connection.post("test")
    assert result.status_code == 200


@patch('requests.post', lambda *args, **kwargs: MockResponse(status_code=200))
def test_post():
    connection = connections.Connection(base_url="http://www.example.com", token="token")
    result = connection.post("test")
    assert result.status_code == 200


@patch('requests.post', lambda *args, **kwargs: MockResponse(status_code=200))
def test_send_status_sucess():
    connection = connections.Connection(base_url="http://www.example.com", token="token")
    result = connection.send_status("dataset_id", Stage.UPLOAD, State.SUCCESS)
    assert result.status_code == 200


@patch('requests.post', lambda *args, **kwargs: MockResponse(status_code=403, reason="Forbidden"))
def test_send_status_forbidden():
    connection = connections.Connection(base_url="http://www.example.com", token="token")
    with pytest.raises(connections.CrunchAPIException, match=r"Failed sending status\.\n403: Forbidden"):
        connection.send_status("dataset_id", Stage.UPLOAD, State.SUCCESS)


