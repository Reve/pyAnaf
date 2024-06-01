import json
import logging
import os
import xml.etree.ElementTree as ET
from configparser import ConfigParser
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import jwt

from pyAnaf.api import AnafResponseError

TESTING = os.environ.get("PYANAF_TESTING", False)
dir_path = os.path.dirname(os.path.realpath(__file__))

config = ConfigParser()
config.read(f"{dir_path}/einvoice_api.ini")

logger = logging.getLogger(__name__)


def parse_element(element):
    parsed_data = {}

    for key, value in element.attrib.items():
        parsed_data[key] = value

    return parsed_data


class AnafAuth:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_url = config["DEFAULT"].get("anaf_auth_url")
        self.token_url = config["DEFAULT"].get("anaf_token_url")

    def set_auth_url(self, url):
        self.auth_url = url

    def set_token_url(self, url):
        self.token_url = url

    def get_auth_url(self):
        """
        Use this URL to get the authorization code
        you need to use a browser in order to input your certificate
        """
        url = self.auth_url
        url += f"?client_id={self.client_id}"
        url += f"&client_secret={self.client_secret}"
        url += "&response_type=code"
        url += f"&redirect_uri={self.redirect_uri}"

        return url

    def get_anaf_token(self, code):
        if code is None:
            return

        url = self.token_url
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

        res_obj = json.loads(response.read())

        return res_obj

    def refresh_anaf_token(self, refresh_token):
        url = self.token_url
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


class EinvoiceApi:
    def __init__(self, access_token, refresh_token, client_id, client_secret, redirect_uri):
        if TESTING:
            self.url = config["testing"].get("anaf_api_url")

        self.url = config["DEFAULT"].get("anaf_api_url")
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth = AnafAuth(self.client_id, self.client_secret, self.redirect_uri)

    def set_url(self, url):
        self.url = url

    def is_token_valid(self):
        try:
            decoded_token = jwt.decode(self.access_token, options={"verify_signature": False})
            exp = datetime.fromtimestamp(decoded_token["exp"], tz=timezone.utc)
            return datetime.now(timezone.utc) >= exp
        except jwt.ExpiredSignatureError:
            logger.error("Token expired")
            return True
        except jwt.InvalidTokenError:
            logger.error("Invalid token")
            return False

    def refresh_access_token(self):
        token_data = self.auth.refresh_anaf_token(self.refresh_token)
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]

    def ensure_token_valid(self):
        if self.is_token_valid():
            self.refresh_access_token()

    def list_messages(self, cif, days=30, filter=None):
        """
        List messages for a CIF
        :param cif: CIF to list messages for
        :param days: number of days to list messages for (optional)
        :param filter: filter messages by type (E,P,T,R) (optional)
        """
        self.ensure_token_valid()

        url = f"{self.url}/listaMesajeFactura?cif={cif}&zile={days}"

        if filter:
            url += f"&filtru={filter}"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
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

        res_obj = json.dumps(response.read().decode())

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
        self.ensure_token_valid()

        url = (
            f"{self.url}/listaMesajePaginatieFactura?cif={cif}&startTime={start_time}&endTime={end_time}&pagina={page}"
        )

        if filter:
            url += f"&filtru={filter}"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
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

        res_obj = json.dumps(response.read().decode())

        return res_obj

    def upload_invoice(self, xml_string, standard, cif, external=False, self_invoice=False):
        """
        Upload invoice to ANAF
        :param standard: standard to use (UBL, CN, CII, RASP)
        :param cif: CIF to upload invoice for
        :param external: external invoice (optional)
        :param self_invoice: self invoice (optional)
        """

        self.ensure_token_valid()

        url = f"{self.url}/upload"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "text/plain",
        }

        params = {
            "standard": standard,
            "cif": cif,
        }

        if external:
            params["external"] = "DA"

        if self_invoice:
            params["selfInvoice"] = "DA"

        url += f"?{urlencode(params)}"

        # load xml from string
        data = xml_string.encode("utf-8")
        request = Request(url, headers=headers, data=data)

        try:
            response = urlopen(request)
        except Exception as e:
            raise AnafResponseError(f"Error uploading invoice: {e}")

        if response.status != 200:
            if response.status == 401 or response.status == 403:
                # TODO trigger refresh token and retry
                raise AnafResponseError("Unauthorized")

            raise AnafResponseError(f"Error uploading invoice: {response.status}")

        xml_data = response.read().decode()
        root = ET.fromstring(xml_data)

        xml_dict = parse_element(root)

        return json.dumps(xml_dict)
