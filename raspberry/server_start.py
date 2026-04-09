import threading
import time


def start_ota_server():

    try:

        print("Starting OTA server...")

        from ota_server.ota_server import run

        run()

    except Exception as e:

        print("OTA server error:", e)


def start_coordinator():

    try:

        print("Starting coordinator...")

        import coordinator

    except Exception as e:

        print("Coordinator error:", e)


def main():

    print("=== CLUSTER SERVER START ===")

    ota_thread = threading.Thread(
        target=start_ota_server,
        daemon=True
    )

    coordinator_thread = threading.Thread(
        target=start_coordinator,
        daemon=True
    )

    ota_thread.start()

    time.sleep(1)

    coordinator_thread.start()

    print("All services started")

    while True:

        time.sleep(10)


if __name__ == "__main__":

    main()