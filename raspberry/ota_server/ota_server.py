"""
Server OTA (Over-The-Air) untuk distribusi firmware dan versi.
Menyediakan endpoint HTTP untuk mengambil version.json dan main.py.
Semua komentar dalam bahasa Indonesia.
"""

from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import os


# =========================
# PENENTUAN DIREKTORI DASAR (PERBAIKAN PENTING)
# =========================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)   # Direktori tempat file ini berada

FIRMWARE_DIR = os.path.join(
    BASE_DIR,
    "firmware"
)   # Subdirektori yang berisi file firmware dan versi

VERSION_FILE = "version.json"   # Nama file informasi versi
FIRMWARE_FILE = "main.py"       # Nama file firmware utama


class OTAHandler(BaseHTTPRequestHandler):
    """
    Handler HTTP sederhana untuk OTA.
    Menangani permintaan GET untuk /version dan /firmware.
    """

    def do_GET(self):
        """
        Menangani permintaan GET.
        Mengarahkan ke pengirim versi atau firmware berdasarkan path.
        """
        if self.path == "/version":
            self.send_version()
        elif self.path == "/firmware":
            self.send_firmware()
        else:
            self.send_error(404)


    # =========================
    # KIRIM VERSI
    # =========================

    def send_version(self):
        """
        Membaca file version.json dan mengirimkannya sebagai response JSON.
        Jika gagal, mengirim error 404.
        """
        path = os.path.join(FIRMWARE_DIR, VERSION_FILE)

        try:
            with open(path, "rb") as f:
                data = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(data))
            self.end_headers()
            self.wfile.write(data)

            print("Version sent")

        except Exception as e:
            print("Version error:", e)
            self.send_error(404)


    # =========================
    # KIRIM FIRMWARE
    # =========================

    def send_firmware(self):
        """
        Membaca file main.py dan mengirimkannya sebagai file biner.
        Jika gagal, mengirim error 404.
        """
        path = os.path.join(FIRMWARE_DIR, FIRMWARE_FILE)

        try:
            with open(path, "rb") as f:
                data = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", len(data))
            self.end_headers()
            self.wfile.write(data)

            print("Firmware sent")

        except Exception as e:
            print("Firmware error:", e)
            self.send_error(404)


# =========================
# MENJALANKAN SERVER
# =========================

def run():
    """
    Membuat dan menjalankan HTTP server pada alamat 0.0.0.0 port 8000.
    Menampilkan informasi direktori firmware yang digunakan.
    Server berjalan terus menerus (serve_forever).
    """
    server = HTTPServer(
        ("0.0.0.0", 8000),
        OTAHandler
    )

    print("OTA server running")
    print("Port:", 8000)
    print("Firmware dir:", FIRMWARE_DIR)

    server.serve_forever()


if __name__ == "__main__":
    # Jika dijalankan langsung, panggil fungsi run()
    run()