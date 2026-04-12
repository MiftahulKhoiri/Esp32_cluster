# raspberry/cli/banner.py

import time
import socket
import os


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
# GET ACTIVE NODE COUNT
# =========================

def get_node_count():

    try:

        from raspberry.coordinator import ready_nodes

        return len(ready_nodes)

    except Exception:

        return 0


# =========================
# GET DIRECTORIES
# =========================

def get_directories():

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
# PRINT BANNER
# =========================

def print_banner():

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