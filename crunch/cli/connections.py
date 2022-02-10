from pathlib import Path
import requests
import re

class CrunchAPIException(Exception):
    """ Raised when there is an error getting information from the API of a crunch site. """
    pass


def get_json_response( base_url, extra_url, token ):
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    if extra_url.startswith("/"):
        extra_url = extra_url[1:]

    url = f"{base_url}/{extra_url}"

    if not token:
        raise CrunchAPIException(f"Please give an authentication token for the {base_url} either through a command line argument or the CRUNCH_TOKEN environment variable.")

    headers = {"Authorization": f"Token {token}" }
    json_response = requests.get(url, headers=headers).json()
    
    if len(json_response.keys()) == 1 and "detail" in json_response:
        raise CrunchAPIException(json_response["detail"])
        
    return json_response
