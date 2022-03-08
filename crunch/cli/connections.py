import requests
import enum

from rich.console import Console

console = Console()

from . import diagnostics

class CrunchAPIException(Exception):
    """ Raised when there is an error getting information from the API of a crunch site. """
    pass


class Connection():
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def get_headers(self):
        if not self.token:
            raise CrunchAPIException(f"Please give an authentication token either through a command line argument or the CRUNCH_TOKEN environment variable.")

        headers = {"Authorization": f"Token {self.token}" }
        return headers

    def absolute_url(self, relative_url):
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
        if relative_url.startswith("/"):
            relative_url = relative_url[1:]

        url = f"{self.base_url}/{relative_url}"
        return url

    def post(self, relative_url, verbose=False, **kwargs):
        url = self.absolute_url(relative_url) 
        result = requests.post(url, headers=self.get_headers(), data=kwargs)
        if verbose:
            console.print(f"Response {result.status_code}: {result.reason}")
        return result

    def add_project(self, project:str, description:str="", details:str="", verbose=False):
        if verbose:
            console.print(f"Adding project '{project}' on the site {self.base_url}")

        return self.post(
            "api/projects/", 
            name=project,
            description=description,
            details=details,
            verbose=verbose,
        )

    def add_dataset(self, project:str, dataset:str, description:str="", details:str="", verbose=False):
        if verbose:
            console.print(f"Adding dataset '{dataset}' to project '{project}' on the site {self.base_url}")

        return self.post(
            "api/datasets/", 
            project=project,
            name=dataset,
            description=description,
            details=details,
            verbose=verbose,
        )

    def add_key_value_attribute(self, url:str, project:str, dataset:str, key:str, value, verbose=False):
        if verbose:
            console.print(f"Adding attribute '{key}'->'{value}' to dataset '{dataset}' in project '{project}' on the hosted site {self.base_url}")

        return self.post(
            url, 
            dataset=dataset,
            key=key,
            value=value,
            verbose=verbose,
        )

    def add_char_attribute(self, project:str, dataset:str, key:str, value:str, verbose=False):
        return self.add_key_value_attribute(
            url="api/attributes/char/", 
            project=project,
            dataset=dataset,
            key=key,
            value=value,
            verbose=verbose,
        )        

    def add_float_attribute(self, project:str, dataset:str, key:str, value:float, verbose=False):
        return self.add_key_value_attribute(
            url="api/attributes/float/", 
            project=project,
            dataset=dataset,
            key=key,
            value=value,
            verbose=verbose,
        )                

    def add_datetime_attribute(self, project:str, dataset:str, key:str, value, format:str="", verbose=False):
        if isinstance(value, str):
            if format:
                from datetime import datetime
                value = datetime.strptime(value, format)
            else:
                from dateutil import parser
                value = parser.parse(value)  

        return self.add_key_value_attribute(
            url="api/attributes/datetime/", 
            project=project,
            dataset=dataset,
            key=key,
            value=value,
            verbose=verbose,
        )                

    def add_integer_attribute(self, project:str, dataset:str, key:str, value:int, verbose=False):
        return self.add_key_value_attribute(
            url="api/attributes/int/", 
            project=project,
            dataset=dataset,
            key=key,
            value=value,
            verbose=verbose,
        )                  

    def add_url_attribute(self, project:str, dataset:str, key:str, value:str, verbose=False):
        return self.add_key_value_attribute(
            url="api/attributes/int/", 
            project=project,
            dataset=dataset,
            key=key,
            value=value,
            verbose=verbose,
        )       

    def add_lat_long_attribute(self, project:str, dataset:str, key:str, latitude, longitude, verbose=False):
        if verbose:
            console.print(f"Adding attribute '{key}'->'{latitude},{longitude}' to dataset '{dataset}' in project '{project}' on the hosted site {self.base_url}")

        return self.post(
            relative_url="api/attributes/lat-long/",
            dataset=dataset,
            key=key,
            latitude=latitude,
            longitude=longitude,
            verbose=verbose,
        )

    def send_status(self, dataset_id, stage, state, note=""):
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
        return self.post("api/statuses/", **data)

    def get_json_response( self, relative_url ):
        url = self.absolute_url(relative_url)

        json_response = requests.get(url, headers=self.get_headers()).json()
        
        if len(json_response.keys()) == 1 and "detail" in json_response:
            raise CrunchAPIException(json_response["detail"])

        return json_response
