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

    def addEndpoint(self, url, target='sync'):
        if target not in ['sync','async']:
            raise AnafError('Invalid target for endpoint. Must be one of \'sync\' or \'async\'')

        self.WS_ENDPOINTS[target] = url;

    def setLimit(self,limit):
        try:
            self.LIMIT = int(limit)
        except:
            raise AnafError('Limit should be an integer')


    def addCUI(self,cui,date):

        if not isinstance(cui, int):
            raise AnafError('CUI should be integer')

        if date is None:
            date = str(datetime.date.today())

        self.cuis[cui] = date

        print (len(self.cuis.items()))




