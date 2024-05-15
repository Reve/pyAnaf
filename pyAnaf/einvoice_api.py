import json
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
    def __init__(self, client_id, client_secret, redirect_uri, refresh_token=None):
        if TESTING:
            self.url = config["testing"].get("anaf_api_url")

        self.url = config["DEFAULT"].get("anaf_api_url")
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.refresh_token = refresh_token

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
        request = Request(url)

        try:
            response = urlopen(request, params)
        except Exception as e:
            raise AnafResponseError(f"Error getting token: {e}")

        if response.status != 200:
            raise AnafResponseError(f"Error getting token: {response.status}")

        res_obj = json.loads(response)

        return res_obj

    def refresh_anaf_token(self, refresh_token):
        url = config["DEFAULT"].get("anaf_token_url")
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "redirect_uri": self.redirect_uri,
        }
        params = urlencode(params).encode("utf-8")
        request = Request(url)

        try:
            response = urlopen(request, params)
        except Exception as e:
            raise AnafResponseError(f"Error refreshing token: {e}")

        if response.status != 200:
            raise AnafResponseError(f"Error refreshing token: {response.status}")

        res_obj = json.loads(response)

        return res_obj

    def list_messages(self, cif, days=30, filter=None):
        """
        List messages for a CIF
        :param cif: CIF to list messages for
        :param days: number of days to list messages for (optional)
        :param filter: filter messages by type (E,P,T,R) (optional)
        """
        if self.refresh_token is None:
            raise AnafResponseError("No refresh token provided")

        url = f"{self.url}/listaMesajeFactura?cif={cif}&days={days}"

        if filter:
            url += f"&filtru={filter}"

        headers = {
            "Authorization": f"Bearer {self.refresh_token}",
        }

        request = Request(url, headers=headers)

        try:
            response = urlopen(request)
        except Exception as e:
            raise AnafResponseError(f"Error listing messages: {e}")

        if response.status != 200:
            if response.status == 401 or response.status == 403:
                # TODO trigger refresh token and retry
                raise AnafResponseError("Unauthorized")

            raise AnafResponseError(f"Error listing messages: {response.status}")

        res_obj = json.loads(response)

        return res_obj

    def list_messages_paginated(self, cif, start_time, end_time, page, filter=None):
        """
        List messages for a CIF with pagination
        :param cif: CIF to list messages for
        :param start_time: start time to list messages for
        :param end_time: end time to list messages for
        :param page: page number
        :param filter: filter messages by type (E,P,T,R) (optional)
        """
        if self.refresh_token is None:
            raise AnafResponseError("No refresh token provided")

        url = f"{self.url}/listaMesajePaginatieFactura?cif={cif}&startTime={start_time}&endTime={end_time}&page={page}"

        if filter:
            url += f"&filtru={filter}"

        headers = {
            "Authorization": f"Bearer {self.refresh_token}",
        }

        request = Request(url, headers=headers)

        try:
            response = urlopen(request)
        except Exception as e:
            raise AnafResponseError(f"Error listing messages: {e}")

        if response.status != 200:
            if response.status == 401 or response.status == 403:
                # TODO trigger refresh token and retry
                raise AnafResponseError("Unauthorized")

            raise AnafResponseError(f"Error listing messages: {response.status}")

        res_obj = json.loads(response)

        return res_obj
