from __future__ import unicode_literals, print_function

import datetime
import sys

PY_3_OR_HIGHER = sys.version_info >= (3, 0)

try:
    import urllib.request as urllib_request
    import urllib.error as urllib_error
except ImportError:
    import urllib2 as urllib_request
    import urllib2 as urllib_error

try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

try:
    import http.client as http_client
except ImportError:
    import httplib as http_client

try:
    import json
except ImportError:
    import simplejson as json

from .models import AnafResultEntry


class AnafError(Exception):
    """
    Base Exception thrown by the Anaf object when there is a
    general error interacting with the API.
    """
    pass


class AnafHTTPError(Exception):
    """
    Exception thrown by the Anaf object when there is an
    HTTP error interacting with anaf.ro.
    """
    pass


class AnafResponseError(Exception):
    """
    Exception thrown by the Anaf object when there is an
    error the response returned from ANAF.
    """
    pass


class Anaf(object):
    WS_ENDPOINTS = {
        'sync': 'https://webservicesp.anaf.ro/PlatitorTvaRest/api/v3/ws/tva',
        'async': 'https://webservicesp.anaf.ro/AsynchWebService/api/v3/ws/tva'
    }
    LIMIT = 500

    def __init__(self):
        self.cuis = {}
        self.result = None
        self.entries = {}

    @staticmethod
    def _validate_cui(cui):
        if not isinstance(cui, int):
            raise AnafError('CUI should be integer')

    @staticmethod
    def _validate_date(date):
        if not isinstance(date, datetime.date):
            raise AnafError('Date should be of type datetime.date')

    @staticmethod
    def _prepare_data(data):
        if PY_3_OR_HIGHER:
            return bytes(data, 'utf-8')
        else:
            return data

    def addEndpoint(self, url, target='sync'):
        if target not in ['sync', 'async']:
            raise AnafError('Invalid target for endpoint. Must be one of \'sync\' or \'async\'')

        self.WS_ENDPOINTS[target] = url;

    def setLimit(self, limit):
        try:
            self.LIMIT = int(limit)
        except:
            raise AnafError('Limit should be an integer')

    def setCUIList(self, cui_list=[], date=None):
        if date is None:
            date = datetime.date.today()

        if len(cui_list) > self.LIMIT:
            raise AnafError('Too many CUIs to be queried. Should limit to %d' % self.LIMIT)

        self._validate_date(date)
        for cui in cui_list:
            self._validate_cui(cui)
            self.cuis[cui] = date

    def addCUI(self, cui, date=None):
        if date is None:
            date = datetime.date.today()

        self._validate_cui(cui)
        self._validate_date(date)

        self.cuis[cui] = date
        if len(self.cuis.items()) > self.LIMIT:
            raise AnafError('Too many CUIs to be queried. Should limit to %d' % self.LIMIT)

    def Request(self):
        # translate cuis entries to ANAF json format
        cui_list = []
        for entry in self.cuis.items():
            cui_list.append(
                {
                    'cui': entry[0],
                    'data': entry[1].isoformat()
                }
            )

        request = urllib_request.Request(self.WS_ENDPOINTS['sync'])
        request.add_header('Content-Type', 'application/json')

        try:
            response = urllib_request.urlopen(request, self._prepare_data(json.dumps(cui_list)))
        except urllib_error.HTTPError as e:
            raise AnafHTTPError('Error connecting to ANAF. Got a %d HTTP code.' % e.code)

        data = response.read()
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        try:
            result = json.loads(data)
        except:
            raise AnafResponseError('Error parsing json response from ANAF.')

        if result['cod'] != 200:
            raise AnafResponseError('%s' % result['message'])

        result = result['found']
        self.result = result

        for entry in result:
            self.entries[entry['cui']] = AnafResultEntry(entry)

    def getCUIData(self, cui):
        if cui not in self.entries.keys():
            return None

        return self.entries[cui]
