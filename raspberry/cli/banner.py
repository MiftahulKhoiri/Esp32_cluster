# raspberry/cli/banner.py

import time
import socket


# =========================
# GET SERVER IP
# =========================

def get_server_ip():

    try:

        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        s.connect(("8.8.8.8", 80))

        ip = s.getsockname()[0]

        s.close()

        return ip

    except Exception:

        return "unknown"


# =========================
# PRINT BANNER
# =========================

def print_banner():

    now = time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    server_ip = get_server_ip()

    print("")
    print("================================================")
    print("           ESP32 CLUSTER MASTER SERVER")
    print("================================================")
    print("")

    print("Services:")
    print("  OTA Server        : starting")
    print("  Coordinator       : starting")
    print("  Database          : ready")
    print("")

    print("Commands:")
    print("")
    print("  upload_program    : kirim program (.py) ke node")
    print("  upload_file       : kirim file data ke node")
    print("  start_train       : jalankan program di node")
    print("")
    print("  status            : lihat node siap")
    print("  nodes             : daftar node terhubung")
    print("  tasks             : task yang sedang berjalan")
    print("")
    print("  ota               : update firmware node")
    print("  help              : tampilkan bantuan")
    print("  exit              : stop server")
    print("")

    print("System:")
    print("  Version           : 1.0")
    print("  Mode              : development")
    print("  Server IP         : {}".format(server_ip))
    print("  Time              : {}".format(now))
    print("")

    print("================================================")
    print("")