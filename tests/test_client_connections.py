import unittest
from unittest.mock import patch
import requests
from crunch.client import connections

class MockResponse():
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


class ConnectionsTestCase(unittest.TestCase):
    @patch('requests.get', lambda *args, **kwargs: MockResponse({"detail": "Not found"}))
    def test_get_json_response_error(self):
        connection = connections.Connection(base_url="http://www.example.com", token="token")

        with self.assertRaises(connections.CrunchAPIException) as context:
            connection.get_json_response("test")

        self.assertTrue("Error getting JSON response from URL 'http://www.example.com/test':" in str(context.exception))
        self.assertTrue("Not found" in str(context.exception))

        
