# raspberry/cli/command_listener.py

import time


# =========================
# IMPORT HANDLER
# =========================

from raspberry.cli.upload_program import (
    upload_program
)

from raspberry.cli.upload_file import (
    upload_file
)

from raspberry.cli.start_train import (
    start_train
)


# =========================
# COMMAND LISTENER
# =========================

def command_listener(services_running):

    while services_running():

        try:

            cmd = input("> ").strip().lower()

            # =====================
            # EXIT
            # =====================

            if cmd == "exit":

                return "exit"

            # =====================
            # UPLOAD PROGRAM
            # =====================

            elif cmd == "upload_program":

                upload_program()

            # =====================
            # UPLOAD FILE
            # =====================

            elif cmd == "upload_file":

                upload_file()

            # =====================
            # START TRAIN
            # =====================

            elif cmd == "start_train":

                start_train()

            # =====================
            # OTA UPDATE
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
            # HELP
            # =====================

            elif cmd == "help":

                print("")
                print("Commands:")
                print("")
                print(" upload_program   : kirim program ke node")
                print(" upload_file      : kirim file data ke node")
                print(" start_train      : jalankan program di node")
                print("")
                print(" status           : lihat node siap")
                print(" nodes            : daftar node")
                print(" tasks            : task berjalan")
                print("")
                print(" ota              : update firmware")
                print(" exit             : keluar")
                print("")

            # =====================
            # EMPTY
            # =====================

            elif cmd == "":

                continue

            # =====================
            # UNKNOWN
            # =====================

            else:

                print("Unknown command")
                print("Type 'help'")

        except Exception as e:

            print("Command error:", e)

            time.sleep(1)