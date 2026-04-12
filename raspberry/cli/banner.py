# raspberry/cli/banner.py

import time


def print_banner():

    print("")
    print("================================")
    print(" ESP32 CLUSTER MASTER SERVER")
    print("================================")
    print("")

    print("Services:")
    print("  OTA Server        : starting")
    print("  Coordinator       : starting")
    print("  Database          : ready")
    print("")

    print("Commands:")
    print("  status            : show ready nodes")
    print("  nodes             : list connected nodes")
    print("  tasks             : show running tasks")
    print("  ota               : trigger OTA update")
    print("  upload            : upload program ke node")
    print("  restart           : restart services")
    print("  exit              : stop server")
    print("")

    now = time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    print("System:")
    print("  Version           : 1.0")
    print("  Mode              : development")
    print("  Time              : {}".format(now))
    print("")