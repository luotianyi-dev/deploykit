import json
import requests
from typing import Optional, Tuple
from platform import python_version, uname

from deploykit_client import display
from deploykit_client.main import __version__
from deploykit_client.config import settings


class SessionError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class Session:
    def __init__(self):
        self.base_url = settings.api_url
        self.session = requests.Session()
        self.headers = {
            "Authorization": f"APIKey {settings.api_key}",
            "User-Agent": f"deployctl/{__version__} "
                          f"(DeployKit; {uname().system} {uname().machine}; Python/{python_version()}) "
                          f"python-requests/{requests.__version__}",
        }
    
    def decode_json_or_none(self, response: requests.Response) -> Tuple[str, dict]:
        try:
            data = response.json()
            return json.dumps(data, indent=4, ensure_ascii=False), data
        except requests.exceptions.JSONDecodeError:
            return response.text, None
    
    def request(self, method: str, path: str, params: Optional[dict] = None, files: Optional[dict] = None) -> dict:
        response = self.session.request(
            method=method,
            url=f"{self.base_url}/{path}",
            headers=self.headers,
            params=params,
            files=files,
        )
        error_detail, data = self.decode_json_or_none(response)
        if (not response.ok) or (data is None):
            display.http_error(response.status_code, error_detail)
            raise SessionError(error_detail)
        return data
