import threading
import time
import sys


services_running = True


# =========================
# START OTA SERVER
# =========================

def start_ota_server():

    try:

        print("Starting OTA server...")

        from raspberry.ota_server.ota_server import run

        run()

    except Exception as e:

        print("OTA server error:", e)


# =========================
# START COORDINATOR
# =========================

def start_coordinator():

    try:

        print("Starting coordinator...")

        import raspberry.coordinator

    except Exception as e:

        print("Coordinator error:", e)


# =========================
# MONITOR
# =========================

def monitor():

    while services_running:

        print("System running...")

        time.sleep(10)


# =========================
# COMMAND LISTENER
# =========================

def command_listener():

    global services_running

    while True:

        try:

            cmd = input("> ").strip()

            if cmd == "exit":

                print("Stopping system...")

                services_running = False

                sys.exit()

            elif cmd == "ota":

                from raspberry.coordinator import client

                print("Sending OTA command...")

                client.publish(
                    "cluster/ota/update",
                    '{"command":"update"}'
                )

            elif cmd == "status":

                from raspberry.coordinator import ready_nodes

                print("Ready nodes:", ready_nodes)

            elif cmd == "help":

                print("")
                print("Commands:")
                print(" status")
                print(" ota")
                print(" exit")
                print("")

        except Exception as e:

            print("Command error:", e)


# =========================
# MAIN
# =========================

def main():

    print("")
    print("================================")
    print(" ESP32 CLUSTER MASTER SERVER")
    print("================================")
    print("")

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

    command_thread = threading.Thread(
        target=command_listener,
        daemon=True
    )

    ota_thread.start()

    time.sleep(1)

    coordinator_thread.start()

    monitor_thread.start()

    command_thread.start()

    while True:

        time.sleep(1)


if __name__ == "__main__":

    main()