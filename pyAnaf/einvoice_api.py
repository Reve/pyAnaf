import os
from configparser import ConfigParser
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from api import AnafResponseError

TESTING = os.environ.get("PYANAF_TESTING", False)
dir_path = os.path.dirname(os.path.realpath(__file__))

config = ConfigParser()
config.read(f"{dir_path}/einvoice_api.ini")


class EinvoiceApi:
    def __init__(self, client_id, client_secret, redirect_uri):
        if TESTING:
            self.url = config["testing"].get("anaf_api_url")

        self.url = config["DEFAULT"].get("anaf_api_url")
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_auth_url(self):
        """
        Use this URL to get the authorization code
        you need to use a browser in order to input your certificate
        """
        url = config["DEFAULT"].get("anaf_auth_url")
        url += f"?client_id={self.client_id}"
        url += f"&client_secret={self.client_secret}"
        url += "&response_type=code"
        url += f"&redirect_uri={self.redirect_uri}"

        return url

    def get_anaf_token(self, code):
        url = config["DEFAULT"].get("anaf_token_url")
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        params = urlencode(params).encode("utf-8")
        request = Request(self.url)

        try:
            response = urlopen(request, params)
        except Exception as e:
            raise AnafResponseError(f"Error getting token: {e}")

        if response.status != 200:
            raise AnafResponseError(f"Error getting token: {response.status}")

        print(response)
