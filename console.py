# coding: utf-8
import argparse
import datetime
import os
import pprint
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from multiprocessing.pool import ThreadPool
from urllib.parse import parse_qs, urlparse

from pyAnaf.einvoice_api import AnafAuth

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
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)

        # Extract the authorization code from the query parameters
        code = query.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"You may now close this window.")

        pp = CustomPrettyPrinter(indent=4)
        pool = ThreadPool(processes=1)

        if code:
            # Exchange code for token in a separate thread
            async_result = pool.apply_async(anaf_auth.get_anaf_token, (code,))
            pp.pprint(async_result.get())

        # Shut down the HTTP server after handling the request
        def shutdown_server(server):
            server.shutdown()

        pool.apply_async(shutdown_server, (httpd,))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="PyAnaf CLI", description="A simple CLI interface for ANAF services")
    parser.add_argument("auth", help="Get Access Token from ANAF", default=None)
    parser.add_argument("cuis", nargs="?", help="CUIs separated by comma", default=None)
    parser.add_argument("--client-id", help="Client ID for ANAF API")
    parser.add_argument("--client-secret", help="Client Secret for ANAF API")
    parser.add_argument("--redirect-uri", help="Redirect URI for ANAF API")

    args = parser.parse_args()

    if args.cuis:
        interogate_cuis(args.cuis)

    if args.auth:
        anaf_auth = AnafAuth(args.client_id, args.client_secret, args.redirect_uri)
        url = anaf_auth.get_auth_url()

        pprint.pprint("=====================")
        pprint.pprint("Here is the URL in case the browser doesn't open automaticaly")
        pprint.pprint(url)  # in case the browser doesn't open by it's self
        pprint.pprint("=====================")

        webbrowser.open_new(anaf_auth.get_auth_url())

        server_address = ("", 8080)
        httpd = HTTPServer(server_address, CallbackServerHandler)
        httpd.serve_forever()
