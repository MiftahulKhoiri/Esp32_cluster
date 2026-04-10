from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler

import os


# =========================
# BASE PATH (CRITICAL FIX)
# =========================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

FIRMWARE_DIR = os.path.join(
    BASE_DIR,
    "firmware"
)

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


    # =========================
    # VERSION
    # =========================

    def send_version(self):

        path = os.path.join(
            FIRMWARE_DIR,
            VERSION_FILE
        )

        try:

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

            print("Version sent")

        except Exception as e:

            print("Version error:", e)

            self.send_error(404)


    # =========================
    # FIRMWARE
    # =========================

    def send_firmware(self):

        path = os.path.join(
            FIRMWARE_DIR,
            FIRMWARE_FILE
        )

        try:

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

            print("Firmware sent")

        except Exception as e:

            print("Firmware error:", e)

            self.send_error(404)


# =========================
# SERVER
# =========================

def run():

    server = HTTPServer(
        ("0.0.0.0", 8000),
        OTAHandler
    )

    print("OTA server running")

    print("Port:", 8000)

    print("Firmware dir:", FIRMWARE_DIR)

    server.serve_forever()


if __name__ == "__main__":

    run()