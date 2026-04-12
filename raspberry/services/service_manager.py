# raspberry/services/service_manager.py

import threading
import time


def start_ota_server():

    try:

        print("[SERVICE] Starting OTA server")

        from raspberry.ota_server.ota_server import run

        run()

    except Exception as e:

        print("[ERROR] OTA server:", e)


def start_coordinator():

    try:

        print("[SERVICE] Starting coordinator")

        import raspberry.coordinator

    except Exception as e:

        print("[ERROR] Coordinator:", e)


def monitor():

    while True:

        print("[MONITOR] System running")

        time.sleep(10)


def start_services():

    ota_thread = threading.Thread(

        target=start_ota_server,
        daemon=True

    )

    coordinator_thread = threading.Thread(

        target=start_coordinator,
        daemon=True

    )

    monitor_thread = threading.Thread(

        target=monitor,
        daemon=True

    )

    ota_thread.start()

    time.sleep(1)

    coordinator_thread.start()

    monitor_thread.start()