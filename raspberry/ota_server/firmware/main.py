"""
Server OTA berbasis Flask untuk distribusi firmware dan versi.
Menyediakan endpoint /firmware untuk mengunduh main.py dan /version untuk versi firmware.
Semua komentar dalam bahasa Indonesia.
"""

from flask import Flask, send_file, jsonify

app = Flask(__name__)   # Membuat instance aplikasi Flask

# Versi firmware yang akan dilaporkan ke node yang meminta
FIRMWARE_VERSION = "1.1"


@app.route("/firmware")
def firmware():
    """
    Endpoint untuk mengunduh file firmware (main.py).
    Menggunakan send_file untuk mengirimkan file langsung.
    """
    return send_file("main.py")


@app.route("/version")
def version():
    """
    Endpoint untuk mendapatkan informasi versi firmware saat ini.
    Mengembalikan JSON dengan key 'version'.
    """
    return jsonify({
        "version": FIRMWARE_VERSION
    })


# Menjalankan server Flask pada semua interface, port 8000
app.run(
    host="0.0.0.0",
    port=8000
)