from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler

import json
import os


FIRMWARE_DIR = "firmware"

VERSION_FILE = "version.json"

FIRMWARE_FILE = "main.py"


class OTAHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/version":

            self.send_version()

        elif self.path == "/firmware":

            self.send_firmware()

        else:

            self.send_error(404)


    def send_version(self):

        path = os.path.join(

            FIRMWARE_DIR,
            VERSION_FILE

        )

        with open(path, "rb") as f:

            data = f.read()

        self.send_response(200)

        self.send_header(

            "Content-Type",
            "application/json"

        )

        self.send_header(

            "Content-Length",
            len(data)

        )

        self.end_headers()

        self.wfile.write(data)


    def send_firmware(self):

        path = os.path.join(

            FIRMWARE_DIR,
            FIRMWARE_FILE

        )

        with open(path, "rb") as f:

            data = f.read()

        self.send_response(200)

        self.send_header(

            "Content-Type",
            "application/octet-stream"

        )

        self.send_header(

            "Content-Length",
            len(data)

        )

        self.end_headers()

        self.wfile.write(data)


def run():

    server = HTTPServer(

        ("0.0.0.0", 8000),

        OTAHandler

    )

    print("OTA server running")

    print("Port:", 8000)

    server.serve_forever()


if __name__ == "__main__":

    run()