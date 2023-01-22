from os import getenv
from typing import Union, Dict
from unicodedata import decimal
import requests
from rest_framework import status as drf_status
import enum
from datetime import datetime, date
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from rich.console import Console
from crunch.django.app.enums import Stage, State

console = Console()

from . import diagnostics

CRUNCH_URL_KEY = "CRUNCH_URL"
CRUNCH_TOKEN_KEY = "CRUNCH_TOKEN"

class CrunchAPIException(Exception):
    """ Raised when there is an error getting information from the API of a crunch site. """
    pass


class Connection():
    """
    An object to manage calls to the REST API of a crunch hosted site.
    """
    def __init__(self, base_url:str = None, token:str = None, verbose:bool = False):
        """
        An object to manage calls to the REST API of a crunch hosted site.

        Args:
            base_url (str, optional): The URL for the endpoint for the project on the crunch hosted site. 
                If not provided then it attempts to use the 'CRUNCH_URL' environment variable.
            token (str, optional): An access token for a user on the crunch hosted site. 
                If not provided then it attempts to use the 'CRUNCH_TOKEN' environment variable.

        Raises:
            CrunchAPIException: If the `base_url` is not provided and it is not available using the 'CRUNCH_URL' environment variable.
            CrunchAPIException: If the `token` is not provided and it is not available using the 'CRUNCH_TOKEN' environment variable.
        """
        self.base_url = base_url or getenv(CRUNCH_URL_KEY, None)
        if not self.base_url:
            raise CrunchAPIException(f"Please provide a base URL to a crunch hosted site. This can be set using the '{CRUNCH_URL_KEY}' environment variable.")

        self.token = token or getenv(CRUNCH_TOKEN_KEY, None)
        if not self.token:
            raise CrunchAPIException(f"Please provide an authentication token. This can be set using the '{CRUNCH_TOKEN_KEY}' environment variable.")

        self.verbose = verbose

    def get_headers(self) -> dict:
        """
        Creates the headers needed to API calls to the REST API on a crunch hosted site.

        Used internally when making GET and POST requests using this class.

        Raises:
            CrunchAPIException: Raised if no valid token is available.

        Returns:
            dict: The headers for API calls as a Python dictionary.
        """
        headers = {"Authorization": f"Token {self.token}" }
        return headers

    def absolute_url(self, relative_url:str) -> str:
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
        if relative_url.startswith("/"):
            relative_url = relative_url[1:]

        url = f"{self.base_url}/{relative_url}"
        return url

    def post(self, relative_url:str, **kwargs) -> requests.Response:
        url = self.absolute_url(relative_url) 
        if self.verbose:
            console.print(f"Posting to {url} : {kwargs}")

        result = requests.post(url, headers=self.get_headers(), data=kwargs)
        if self.verbose:
            console.print(f"Response {result.status_code}: {result.reason}")

        if result.status_code >= 400:
            console.print(f"Failed posting to {url} : {kwargs}")
            console.print(result.json())
        return result

    def add_project(self, project:str, description:str="", details:str="") -> requests.Response:
        """
        Creates a new project on a hosted django-crunch site.

        Args:
            project (str): The name of the new crunch project.
            description (str, optional): A brief description of this new project. Defaults to "".
            details (str, optional): A long description of this project in Markdown format. Defaults to "".

        Returns:
            requests.Response: The request object from posting to the crunch API.
        """
        if self.verbose:
            console.print(f"Adding project '{project}' on the site {self.base_url}")

        return self.post(
            "api/projects/", 
            name=project,
            description=description,
            details=details,
        )

    def add_dataset(self, project:str, dataset:str, description:str="", details:str="") -> requests.Response:
        """
        Creates a new dataset and adds it to a project on a hosted django-crunch site.

        Args:
            project (str): The slug of the project that this dataset is to be added to.
            dataset (str): The name of the new dataset.
            description (str, optional): A brief description of this new dataset. Defaults to "".
            details (str, optional): A long description of this dataset in Markdown format. Defaults to "".

        Returns:
            requests.Response: The request object from posting to the crunch API.
        """
        if self.verbose:
            console.print(f"Adding dataset '{dataset}' to project '{project}' on the site {self.base_url}")

        return self.post(
            "api/datasets/", 
            parent=project,
            name=dataset,
            description=description,
            details=details,
        )

    def add_item(self, parent:str, item:str, description:str="", details:str="") -> requests.Response:
        """
        Creates a new item on a hosted django-crunch site.

        Args:
            parent (str): The slug of the parent item that this item is to be added to.
            item (str): The name of the new item.
            description (str, optional): A brief description of this new dataset. Defaults to "".
            details (str, optional): A long description of this dataset in Markdown format. Defaults to "".

        Returns:
            requests.Response: The request object from posting to the crunch API.
        """
        if self.verbose:
            console.print(f"Adding item '{item}' to parent '{parent}' on the site {self.base_url}")

        return self.post(
            "api/items/", 
            parent=parent,
            name=item,
            description=description,
            details=details,
        )

    def add_key_value_attribute(self, url:str, item:str, key:str, value) -> requests.Response:
        """
        Adds an attribute as a key/value pair on an item. 
        
        This is mainly used by other methods on this class to add attributes with specific types.

        Args:
            url (str): The relative URL for adding this type of attribute on the crunch site. For this, see urls.py in the crunch Django app.
            item (str): The slug for the item.
            key (str): The key for this attribute.
            value: The data to be used for this attribute. The object needs to be serializable.

        Returns:
            requests.Response: The request object from posting to the crunch API.
        """
        if self.verbose:
            console.print(f"Adding attribute '{key}'->'{value}' to item '{item}' on the hosted site {self.base_url}")

        return self.post(
            url, 
            item=item,
            key=key,
            value=value,
        )

    def add_char_attribute(self, item:str, key:str, value:str) -> requests.Response:
        """
        Adds an attribute as a key/value pair on a dataset when the value is a string of characters. 

        Args:
            project (str): The slug for the project.
            dataset (str): The slug for the dataset.
            key (str): The key for this attribute.
            value (str): The string of characters for this attribute.

        Returns:
            requests.Response: The request object from posting to the crunch API.
        """
        return self.add_key_value_attribute(
            url="api/attributes/char/", 
            item=item,
            key=key,
            value=value,
        ) 

    def add_attributes(self, item:str, **kwargs):
        """
        Adds multiple attributes as a key/value pairs on a dataset. 

        Each type is inferred from the type of the value.

        Args:
            item (str): The slug for the item.
            **kwargs: key/value pairs to add as char attributes.
        """
        url_validator = URLValidator()
        for key, value in kwargs.items():
            if isinstance(value, str):
                try: 
                    url_validator(value)
                    self.add_url_attribute(item=item, key=key, value=value)
                except ValidationError:
                    self.add_char_attribute(item=item, key=key, value=value)
            elif isinstance(value, float):
                self.add_float_attribute(item=item, key=key, value=value)
            elif isinstance(value, bool): # This needs to be before the 'int' one because bools are also integers in python
                self.add_boolean_attribute(item=item, key=key, value=value)
            elif isinstance(value, int):
                self.add_integer_attribute(item=item, key=key, value=value)
            elif isinstance(value, datetime):
                self.add_datetime_attribute(item=item, key=key, value=value)
            elif isinstance(value, date):
                self.add_date_attribute(item=item, key=key, value=value)
            else:
                raise CrunchAPIException(f"Cannot infer type of value '{value}' ({type(value).__name__}). (The key was '{key}')")

    def add_float_attribute(self, item:str, key:str, value:float) -> requests.Response:
        """
        Adds an attribute as a key/value pair on a dataset when the value is a float. 

        Args:
            item (str): The slug for the item.
            key (str): The key for this attribute.
            value (str): The float value for this attribute.

        Returns:
            requests.Response: The request object from posting to the crunch API.
        """
        return self.add_key_value_attribute(
            url="api/attributes/float/", 
            item=item,
            key=key,
            value=value,
        )                

    def add_datetime_attribute(self, item:str, key:str, value:Union[datetime,str], format:str="") -> requests.Response:
        """
        Adds an attribute as a key/value pair on a dataset when the value is a datetime. 

        Args:
            item (str): The slug for the item.
            key (str): The key for this attribute.
            value (Union[datetime,str]): The value for this attribute as a datetime or a string.
            format (str): If the `value` is a string then this format string can be used with datetime.strptime to convert to a datetime object. If no format is given then the string is interpreted using dateutil.parser.

        Returns:
            requests.Response: The request object from posting to the crunch API.
        """
        if isinstance(value, str):
            if format:
                value = datetime.strptime(value, format)
            else:
                from dateutil import parser
                value = parser.parse(value)  

        return self.add_key_value_attribute(
            url="api/attributes/datetime/", 
            item=item,
            key=key,
            value=value,
        )                

    def add_date_attribute(self, item:str, key:str, value:Union[date,str], format:str="") -> requests.Response:
        """
        Adds an attribute as a key/value pair on a dataset when the value is a datetime. 

        Args:
            item (str): The slug for the item.
            key (str): The key for this attribute.
            value (Union[date,str]): The value for this attribute as a date or a string.
            format (str): If the `value` is a string then this format string can be used with datetime.strptime to convert to a date object. If no format is given then the string is interpreted using dateutil.parser.

        Returns:
            requests.Response: The request object from posting to the crunch API.
        """
        if isinstance(value, str):
            if format:
                value = datetime.strptime(value, format)
            else:
                from dateutil import parser
                value = parser.parse(value)  

        if isinstance(value, datetime):
            value = value.date()

        return self.add_key_value_attribute(
            url="api/attributes/date/", 
            item=item,
            key=key,
            value=value,
        )                

    def add_integer_attribute(self, item:str, key:str, value:int) -> requests.Response:
        """
        Adds an attribute as a key/value pair on a dataset when the value is an integer. 

        Args:
            item (str): The slug for the item.
            key (str): The key for this attribute.
            value (int): The integer value for this attribute.

        Returns:
            requests.Response: The request object from posting to the crunch API.
        """
        return self.add_key_value_attribute(
            url="api/attributes/int/", 
            item=item,
            key=key,
            value=value,
        )               
        
    def add_filesize_attribute(self, item:str, key:str, value:int) -> requests.Response:
        """
        Adds an attribute as a key/value pair on a dataset when the value is an filesize. 

        Args:
            item (str): The slug for the item.
            key (str): The key for this attribute.
            value (int): The size of the file in bytes.

        Returns:
            requests.Response: The request object from posting to the crunch API.
        """
        return self.add_key_value_attribute(
            url="api/attributes/filesize/", 
            item=item,
            key=key,
            value=value,
        )               
                
    def add_boolean_attribute(self, item:str, key:str, value:bool) -> requests.Response:
        """
        Adds an attribute as a key/value pair on a dataset when the value is a boolean. 

        Args:
            item (str): The slug for the item.
            key (str): The key for this attribute.
            value (bool): The integer value for this attribute.

        Returns:
            requests.Response: The request object from posting to the crunch API.
        """
        return self.add_key_value_attribute(
            url="api/attributes/bool/", 
            item=item,
            key=key,
            value=value,
        )                  

    def add_url_attribute(self, item:str, key:str, value:str) -> requests.Response:
        """
        Adds an attribute as a key/value pair on a dataset when the value is a URL. 

        Args:
            item (str): The slug for the item.
            key (str): The key for this attribute.
            value (str): The str value for this attribute.

        Returns:
            requests.Response: The request object from posting to the crunch API.
        """
        return self.add_key_value_attribute(
            url="api/attributes/url/", 
            item=item,
            key=key,
            value=value,
        )       

    def add_lat_long_attribute(self, item:str, key:str, latitude:Union[str,float,decimal], longitude:Union[str,float,decimal]) -> requests.Response:
        """
        Adds an attribute as a key/value pair on a dataset when the value is a coordinate with latitude and longitude. 

        Args:
            item (str): The slug for the item.
            key (str): The key for this attribute.
            latitude (Union[str,float,decimal]): The latitude for this coordinate.
            longitude (Union[str,float,decimal]): The longitude for this coordinate.

        Returns:
            requests.Response: The request object from posting to the crunch API.
        """
        if self.verbose:
            console.print(f"Adding attribute '{key}'->'{latitude},{longitude}' to item '{item}' on the hosted site {self.base_url}")

        return self.post(
            relative_url="api/attributes/lat-long/",
            item=item,
            key=key,
            latitude=latitude,
            longitude=longitude,
        )

    def send_status(self, dataset_id:str, stage:Stage, state:State, note:str="") -> requests.Response:
        """
        Sends an update of the status of one stage in processing a dataset.

        Args:
            dataset_id (str): The ID of the dataset for this status update.
            stage (Stage): The stage of this status update.
            state (State): The state of this status update.
            note (str, optional): A note which gives more information to this status update. Defaults to "".

        Raises:
            CrunchAPIException: If there was an error posting this status update to the API.

        Returns:
            requests.Response: The resulting response from the request to the API.
        """
        data = dict(
            dataset=dataset_id,
            stage=stage.value,
            state=state.value,
            note=note,
        )
        data.update( diagnostics.get_diagnostics() )
        result = self.post("api/statuses/", **data)
        if result.status_code >= 400:
            raise CrunchAPIException(f"Failed sending status.\n{result.status_code}: {result.reason}\nData: {data}")

        return result

    def get_request(self, relative_url:str):
        url = self.absolute_url(relative_url)
        return requests.get(url, headers=self.get_headers())
        
    def get_json_response( self, relative_url:str ) -> Dict:
        """
        Requests JSON data from the API of a crunch hosted site and returns it as a dictionary.

        Args:
            relative_url (str): The URL path relative to the base URL of the endpoint for the project on the crunch hosted site.

        Raises:
            CrunchAPIException: Raises exception if there is an error getting a JSON response from the API.

        Returns:
            Dict: The JSON data from the API encoded as a dictionary.
        """
        response = self.get_request(relative_url)
        json_response = response.json()
        
        if len(json_response.keys()) == 1 and "detail" in json_response:
            raise CrunchAPIException(
                f"Error getting JSON response from URL '{self.absolute_url(relative_url)}':\n" +
                f"{json_response['detail']}"
            )

        return json_response
