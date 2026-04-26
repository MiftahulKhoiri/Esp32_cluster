# Import modul waktu
import time

# Import fungsi Access Point
from ap_wifi import (
    get_ap,
    get_connected_clients
)

# Ambil konfigurasi interval
from config import NODE_SCAN_INTERVAL


# =========================
# GLOBAL
# =========================

# Waktu terakhir scan node (ms)
_last_scan = 0

# Cache jumlah node
_cached_count = 0

# Cache daftar node
_cached_clients = []


# =========================
# FORMAT MAC
# =========================

def format_mac(mac_bytes):
    """
    Mengubah MAC address dari bytes menjadi string format:
    AA:BB:CC:DD:EE:FF
    """

    try:
        return ":".join(
            "{:02X}".format(b)
            for b in mac_bytes
        )
    except Exception:
        return "00:00:00:00:00:00"


# =========================
# SCAN CLIENTS
# =========================

def scan_clients():
    """
    Melakukan scan perangkat yang terhubung ke Access Point.
    Hasil disimpan dalam cache agar tidak melakukan scan terlalu sering.
    """

    global _last_scan
    global _cached_count
    global _cached_clients

    now = time.ticks_ms()

    # Hindari scan terlalu sering
    if time.ticks_diff(now, _last_scan) < NODE_SCAN_INTERVAL * 1000:
        return

    _last_scan = now

    try:
        stations = get_connected_clients()

        clients = []

        for station in stations:
            try:
                mac = format_mac(station[0])

                # Beberapa firmware hanya mengembalikan MAC
                if len(station) > 1:
                    ip = station[1]
                else:
                    ip = "0.0.0.0"

                clients.append({
                    "mac": mac,
                    "ip": ip
                })

            except Exception:
                continue

        _cached_clients = clients
        _cached_count = len(clients)

    except Exception as e:
        print("Node scan error:", e)
        _cached_clients = []
        _cached_count = 0


# =========================
# GET CLIENT COUNT
# =========================

def get_node_count():
    """
    Mengembalikan jumlah node yang terhubung.
    Menggunakan cache untuk menghindari overhead scan.
    """

    scan_clients()

    return _cached_count


# =========================
# GET CLIENT LIST
# =========================

def get_node_list():
    """
    Mengembalikan daftar node yang terhubung.
    Setiap item berisi:
        mac
        ip
    """

    scan_clients()

    return _cached_clients


# =========================
# GET FIRST NODE
# =========================

def get_first_node():
    """
    Mengembalikan node pertama yang terhubung.
    Berguna untuk debugging atau monitoring sederhana.
    """

    scan_clients()

    if _cached_clients:
        return _cached_clients[0]

    return None


# =========================
# IS NODE CONNECTED
# =========================

def is_any_node_connected():
    """
    Memeriksa apakah ada node yang terhubung.
    """

    return get_node_count() > 0


# =========================
# GET STATUS SUMMARY
# =========================

def get_status_summary():
    """
    Mengembalikan ringkasan status node dalam dictionary.
    Digunakan oleh main loop untuk update display.
    """

    return {
        "count": get_node_count(),
        "connected": is_any_node_connected()
    }