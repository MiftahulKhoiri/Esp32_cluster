# raspberry/cli/banner.py
"""
Modul banner untuk menampilkan informasi server cluster.
Menampilkan IP, jumlah node, direktori, dan konfigurasi.
Semua komentar dalam bahasa Indonesia.
"""

import time
import socket
import os


# =========================
# MENDAPATKAN IP SERVER
# =========================

def get_server_ip():
    """
    Mendapatkan alamat IP lokal server dengan menggunakan socket.
    Membuka koneksi UDP ke DNS Google (8.8.8.8) untuk mengetahui IP lokal.
    Jika gagal, mengembalikan "unknown".
    """
    try:
        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]   # IP yang digunakan untuk koneksi keluar
        s.close()
        return ip
    except Exception:
        return "unknown"


# =========================
# MENDAPATKAN JUMLAH NODE AKTIF
# =========================

def get_node_count():
    """
    Mengambil jumlah node yang sedang dalam status siap (ready) dari koordinator.
    Mengimpor modul coordinator dan mengambil panjang himpunan ready_nodes.
    Jika gagal (misal coordinator belum berjalan), mengembalikan 0.
    """
    try:
        from raspberry.coordinator import ready_nodes
        return len(ready_nodes)
    except Exception:
        return 0


# =========================
# MENDAPATKAN DIREKTORI UTAMA
# =========================

def get_directories():
    """
    Menghasilkan path direktori penting:
    - programs : tempat program yang akan didistribusikan
    - data     : tempat data masukan
    - hasil    : tempat hasil penggabungan
    Semua berada di bawah direktori cli.
    """
    base_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    program_dir = os.path.join(
        base_dir,
        "programs"
    )
    data_dir = os.path.join(
        base_dir,
        "data"
    )
    result_dir = os.path.join(
        base_dir,
        "hasil"
    )

    return program_dir, data_dir, result_dir


# =========================
# MENCETAK BANNER INFORMASI
# =========================

def print_banner():
    """
    Mencetak informasi server secara lengkap:
    - Layanan aktif (OTA, Coordinator, Database)
    - Versi, mode, IP server, jumlah node, MQTT broker
    - Direktori penting (programs, data, results)
    - Konfigurasi runtime (chunk size, auto train, retry limit)
    - Waktu mulai server
    Semua ditampilkan dalam format yang mudah dibaca.
    """
    now = time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    server_ip = get_server_ip()
    node_count = get_node_count()
    program_dir, data_dir, result_dir = get_directories()

    print("")
    print("================================================")
    print("           ESP32 CLUSTER MASTER SERVER")
    print("================================================")
    print("")

    print("Services:")
    print("  OTA Server        : running")
    print("  Coordinator       : running")
    print("  Database          : ready")
    print("")

    print("System:")
    print("")
    print("  Version           : 1.0")
    print("  Mode              : development")
    print("  Server IP         :", server_ip)
    print("  Active Nodes      :", node_count)
    print("  MQTT Broker       : local")
    print("")

    print("Directories:")
    print("  Programs          :", program_dir)
    print("  Data              :", data_dir)
    print("  Results           :", result_dir)
    print("")

    print("Runtime Config:")
    print("  Chunk Size        : 8192 bytes")
    print("  Auto Train        : enabled")
    print("  Retry Limit       : enabled")
    print("")

    print("Time:")
    print("  Start Time        :", now)
    print("")

    print("================================================")
    print("")