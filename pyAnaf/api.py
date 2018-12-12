# encoding: utf-8
from __future__ import unicode_literals, print_function

import datetime

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


class AnafError(Exception):
    """
    Base Exception thrown by the Anaf object when there is a
    general error interacting with the API.
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

    def __validate_cui(self, cui):
        if not isinstance(cui, int):
            raise AnafError('CUI should be integer')

    def __validate_date(self, date):
        if not isinstance(date, datetime.date):
            raise AnafError('Date should be of type datetime.date')

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
        """Sets the CUI list

        :param cui_list: A list of unique fiscal code numbers
        :param date: A single date

        :type cui_list: list
        :type date: datetime.date type

        :return:
        """

        if date is None:
            date = datetime.date.today()

        if len(cui_list) > self.LIMIT:
            raise AnafError('Too many CUIs to be queried. Should limit to %d' % self.LIMIT)

        self.__validate_date(date)
        for cui in cui_list:
            self.__validate_cui(cui)
            self.cuis[cui] = date

    def addCUI(self, cui, date=None):
        """ Adds CUI entry to the list of CUIs

        :param cui: A unique fiscal code number in the form of an integer  (e.g. 273663)
        :param date: A datetime.date object

        :type cui: int
        :type date: datetime.date type

        :raise AnafError: If invalid cui and date are provided, or CUI limit is exceeded
        """

        if date is None:
            date = datetime.date.today()

        self.__validate_cui(cui)
        self.__validate_date(date)

        self.cuis[cui] = date
        if len(self.cuis.items()) > self.LIMIT:
            raise AnafError('Too many CUIs to be queried. Should limit to %d' % self.LIMIT)

    def Query(self):
        """

        :return:
        """

        # translate cuis entries to ANAF json format
        cui_list = []
        for entry in self.cuis.items():
            cui_list.append(
                {
                    'cui': entry[0],
                    'data': entry[1].isoformat()
                }
            )
        print (cui_list)
