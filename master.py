import threading
import time
import sys
import signal
from toolsupdate.bootstrap import bootstrap


# =========================
# GLOBAL STATE
# =========================

services_running = True


# =========================
# PRINT BANNER
# =========================

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


# =========================
# START OTA SERVER
# =========================

def start_ota_server():

    try:

        print("[SERVICE] Starting OTA server")

        from raspberry.ota_server.ota_server import run

        run()

    except Exception as e:

        print("[ERROR] OTA server:", e)


# =========================
# START COORDINATOR
# =========================

def start_coordinator():

    try:

        print("[SERVICE] Starting coordinator")

        import raspberry.coordinator

    except Exception as e:

        print("[ERROR] Coordinator:", e)


# =========================
# MONITOR SYSTEM
# =========================

def monitor():

    while services_running:

        try:

            print(
                "[MONITOR] System running"
            )

            time.sleep(10)

        except Exception as e:

            print("[MONITOR ERROR]", e)


# =========================
# SAFE SHUTDOWN
# =========================

def shutdown():

    global services_running

    print("")
    print("Stopping system...")

    services_running = False

    time.sleep(1)

    print("System stopped")

    sys.exit(0)


# =========================
# SIGNAL HANDLER
# =========================

def handle_signal(sig, frame):

    shutdown()


signal.signal(
    signal.SIGINT,
    handle_signal
)


# =========================
# COMMAND LISTENER
# =========================

def command_listener():

    global services_running

    while services_running:

        try:

            cmd = input("> ").strip().lower()

            # =====================
            # EXIT
            # =====================

            if cmd == "exit":

                shutdown()

            # =====================
            # OTA
            # =====================

            elif cmd == "ota":

                try:

                    from raspberry.coordinator import client

                    print("Sending OTA command")

                    client.publish(

                        "cluster/ota/update",

                        '{"command":"update"}'

                    )

                except Exception as e:

                    print("OTA failed:", e)

            # =====================
            # STATUS
            # =====================

            elif cmd == "status":

                try:

                    from raspberry.coordinator import ready_nodes

                    print("")
                    print("Ready nodes:")
                    print(ready_nodes)
                    print("")

                except Exception as e:

                    print("Status error:", e)

            # =====================
            # NODES
            # =====================

            elif cmd == "nodes":

                try:

                    from raspberry.coordinator import node_last_seen

                    print("")
                    print("Nodes:")

                    if not node_last_seen:

                        print("  (no nodes connected)")

                    for node in node_last_seen:

                        print("  -", node)

                    print("")

                except Exception as e:

                    print("Nodes error:", e)

            # =====================
            # TASKS
            # =====================

            elif cmd == "tasks":

                try:

                    from raspberry.coordinator import running_tasks

                    print("")
                    print("Running tasks:")

                    if not running_tasks:

                        print("  (no running tasks)")

                    for task_id in running_tasks:

                        print("  -", task_id)

                    print("")

                except Exception as e:

                    print("Tasks error:", e)

            # =====================
            # RESTART
            # =====================

            elif cmd == "restart":

                print("")
                print("Restart requested")
                print("Please restart manually:")
                print("")
                print("python master.py")
                print("")

            # =====================
            # HELP
            # =====================

            elif cmd == "help":

                print("")
                print("Commands:")
                print(" status")
                print(" nodes")
                print(" tasks")
                print(" ota")
                print(" restart")
                print(" exit")
                print("")

            # =====================
            # EMPTY INPUT
            # =====================

            elif cmd == "":

                continue

            # =====================
            # UNKNOWN
            # =====================

            else:

                print("Unknown command")

                print("Type 'help'")

        except KeyboardInterrupt:

            shutdown()

        except Exception as e:

            print("Command error:", e)


# =========================
# MAIN
# =========================

def main():

    print_banner()

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

    while services_running:

        time.sleep(1)


# =========================

if __name__ == "__main__":

    bootstrap()
    main()