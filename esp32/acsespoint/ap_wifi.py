# Import modul network dan waktu
import network
import time

# Ambil konfigurasi dari file config
from config import (
    SSID,
    PASSWORD,
    CHANNEL,
    MAX_CLIENTS,
    AP_IP,
    SUBNET,
    GATEWAY
)


# =========================
# GLOBAL
# =========================

# Objek Access Point global
_ap = None


# =========================
# START ACCESS POINT
# =========================

def start_access_point():
    """
    Menginisialisasi dan menjalankan WiFi Access Point (mode AP).
    Mengatur SSID, password, channel, jumlah maksimum client,
    serta konfigurasi alamat IP statis.
    Mengembalikan objek Access Point yang aktif.
    """

    global _ap

    # Buat interface Access Point
    _ap = network.WLAN(network.AP_IF)

    # Aktifkan interface jika belum aktif
    if not _ap.active():
        _ap.active(True)
        time.sleep(1)

    print("Starting Access Point")

    try:
        # Konfigurasi Access Point
        _ap.config(
            essid=SSID,
            password=PASSWORD,
            channel=CHANNEL,
            max_clients=MAX_CLIENTS,
            authmode=network.AUTH_WPA_WPA2_PSK
        )

        # Set IP statis
        _ap.ifconfig((
            AP_IP,
            SUBNET,
            GATEWAY,
            GATEWAY
        ))

        time.sleep(1)

        print("Access Point started")
        print("SSID :", SSID)
        print("IP   :", _ap.ifconfig()[0])

    except Exception as e:
        print("AP start error:", e)

    return _ap


# =========================
# GET AP
# =========================

def get_ap():
    """
    Mengembalikan objek Access Point yang sedang aktif.
    Jika belum dibuat, akan membuat instance baru.
    """

    global _ap

    if _ap is None:
        _ap = network.WLAN(network.AP_IF)

    return _ap


# =========================
# GET IP ADDRESS
# =========================

def get_ip():
    """
    Mengembalikan alamat IP Access Point.
    Jika gagal, mengembalikan string '0.0.0.0'.
    """

    try:
        ap = get_ap()
        return ap.ifconfig()[0]
    except Exception:
        return "0.0.0.0"


# =========================
# GET CONNECTED STATIONS
# =========================

def get_connected_clients():
    """
    Mengembalikan daftar perangkat (station) yang terhubung
    ke Access Point.
    Setiap item berisi tuple:
        (MAC address, IP address)
    Jika gagal, mengembalikan list kosong.
    """

    try:
        ap = get_ap()

        # Method standar ESP32 MicroPython
        stations = ap.status("stations")

        return stations

    except Exception as e:
        print("Station list error:", e)
        return []


# =========================
# GET CLIENT COUNT
# =========================

def get_client_count():
    """
    Mengembalikan jumlah client yang saat ini terhubung
    ke Access Point.
    """

    stations = get_connected_clients()

    try:
        return len(stations)
    except Exception:
        return 0


# =========================
# IS ACTIVE
# =========================

def is_active():
    """
    Memeriksa apakah Access Point sedang aktif.
    Mengembalikan True jika aktif.
    """

    try:
        ap = get_ap()
        return ap.active()
    except Exception:
        return False