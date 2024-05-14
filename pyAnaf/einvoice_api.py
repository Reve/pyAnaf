import os
from urllib.request import Request
from configparser import ConfigParser

TESTING = os.environ.get("PYANAF_TESTING", False)

config = ConfigParser()
config.read("einvoice_api.cfg")


class EinvoiceApi:
    def __init__(self, client_id, client_secret, redirect_uri):
        if TESTING:
            self.url = config.get("TESTING", "ANAF_API_URL")

        self.url = config.get("GENERAL", "ANAF_API_URL")
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_auth_url(self):
        """
        Use this URL to get the authorization code
        you need to use a browser in order to input your certificate
        """
        url = config.get("GENERAL", "ANAF_AUTHORIZE_URL")
        url += f"?client_id={self.client_id}"
        url += f"&client_secret={self.client_secret}"
        url += f"&response_type=code"
        url += f"&redirect_uri={self.redirect_uri}"

        return url

    def get_anaf_token(self, code):
        url = config.get("GENERAL", "ANAF_TOKEN_URL")
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        request = Request(self.url)
