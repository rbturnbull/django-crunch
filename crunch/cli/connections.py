import requests
import enum

from . import diagnostics

class CrunchAPIException(Exception):
    """ Raised when there is an error getting information from the API of a crunch site. """
    pass


def get_headers(token):
    if not token:
        raise CrunchAPIException(f"Please give an authentication token for the {base_url} either through a command line argument or the CRUNCH_TOKEN environment variable.")

    headers = {"Authorization": f"Token {token}" }
    return headers

def mkurl(base_url, extra_url):
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    if extra_url.startswith("/"):
        extra_url = extra_url[1:]

    url = f"{base_url}/{extra_url}"
    return url

def get_json_response( base_url, extra_url, token ):
    url = mkurl(base_url, extra_url)
    json_response = requests.get(url, headers=get_headers(token)).json()
    
    if len(json_response.keys()) == 1 and "detail" in json_response:
        raise CrunchAPIException(json_response["detail"])

    return json_response


def send_status(base_url, dataset_id, token, stage, state, note=""):
    url = mkurl(base_url, "api/statuses/") 

    if isinstance(stage, enum.Enum):
        stage = stage.value
    if isinstance(state, enum.Enum):
        state = state.value

    data = dict(
        dataset=dataset_id,
        stage=stage,
        state=state,
        note=note,
    )
    data.update( diagnostics.get_diagnostics() )
    print(data)
    return requests.post(url, headers=get_headers(token), data=data)
