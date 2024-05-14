# coding: utf-8
import argparse
import datetime
import os
import pprint
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from einvoice_api import EinvoiceApi

try:
    from pyAnaf.api import Anaf
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from pyAnaf.api import Anaf


class CustomPrettyPrinter(pprint.PrettyPrinter):
    def format(self, object, context, maxlevels, level):
        # print (type(object))
        # print (object)
        # if isinstance(object, str):
        #     return (object.encode('utf8'), True, False)
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)


def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def interogate_cuis(cuis):
    limit = 5
    cuis = sys.argv[1].split(",")

    try:
        limit = int(sys.argv[2])
    except Exception as e:
        print_err(e)

    today = datetime.date.today()
    anaf = Anaf()
    anaf.setLimit(limit)

    for cui in cuis:
        try:
            anaf.addCUI(int(cui), date=today)
        except Exception as e:
            print_err(e)

    anaf.Request()
    pp = CustomPrettyPrinter(indent=4)

    for entry in anaf.result:
        pp.pprint(entry)


class CallbackServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        query = urlparse.parse_qs(parsed_path.query)

        # Extract the authorization code from the query parameters
        code = query.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"You may now close this window.")

        if code:
            # Exchange code for token in a separate thread
            threading.Thread(target=einvoice.get_anaf_token, args=(code,)).start()

        # Shut down the HTTP server after handling the request
        def shutdown_server(server):
            server.shutdown()

        threading.Thread(target=shutdown_server, args=(httpd,)).start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="PyAnaf CLI", description="A simple CLI interface for ANAF services")
    parser.add_argument("auth", help="Get Access Token from ANAF", default=None)
    parser.add_argument("-c", "--cuis", help="CUIs separated by comma", default=None)

    args = parser.parse_args()

    if args.cuis:
        interogate_cuis(args.cuis)

    if args.auth:
        einvoice = EinvoiceApi("test", "test", "http://localhost:8080")
        url = einvoice.get_auth_url()
        print(url)
        webbrowser.open_new(einvoice.get_auth_url())
        # webbrowser.open_new("https://google.ro")

        server_address = ("", 8080)
        httpd = HTTPServer(server_address, CallbackServerHandler)
        httpd.serve_forever()
