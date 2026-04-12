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
# COMMAND MAP
# =========================

COMMAND_MAP = {

    "0": "exit",
    "1": "upload_program",
    "2": "upload_file",
    "3": "start_train",
    "4": "ota",
    "5": "status",
    "6": "nodes",
    "7": "tasks"

}


# =========================
# HELP MENU
# =========================

def show_help():

    print("")
    print("================================================")
    print("                  COMMAND HELP")
    print("================================================")
    print("")

    print(" [0]  = (exit)")
    print("      Menghentikan server dan semua service")
    print("")

    print(" [1]  = (upload_program)")
    print("      Mengirim file program (.py) ke semua node")
    print("      Digunakan sebelum menjalankan training")
    print("")

    print(" [2]  = (upload_file)")
    print("      Mengirim dataset ke node")
    print("      File akan otomatis di-split menjadi beberapa bagian")
    print("")

    print(" [3]  = (start_train)")
    print("      Menjalankan program yang sudah di-upload")
    print("      Node akan mulai memproses data")
    print("")

    print(" [4]  = (ota update)")
    print("      Mengirim perintah update firmware ke semua node")
    print("      Node akan download firmware terbaru lalu restart")
    print("")

    print(" [5]  = (status)")
    print("      Menampilkan daftar node yang siap menerima task")
    print("")

    print(" [6]  = (nodes)")
    print("      Menampilkan semua node yang aktif dan terhubung ke server")
    print("")

    print(" [7]  = (tasks)")
    print("      Menampilkan task yang sedang berjalan")
    print("")

    print(" [help] = (help)")
    print("      Menampilkan menu bantuan ini")
    print("")

    print("================================================")
    print("")

# =========================
# COMMAND LISTENER
# =========================

def command_listener(services_running):

    while services_running():

        try:

            cmd = input("> ").strip().lower()

            # =====================
            # HELP
            # =====================

            if cmd == "help":

                show_help()

                continue

            # =====================
            # VALIDATE NUMBER
            # =====================

            if cmd not in COMMAND_MAP:

                print("Unknown command")
                print("Type 'help'")
                continue

            action = COMMAND_MAP[cmd]

            # =====================
            # EXIT
            # =====================

            if action == "exit":

                return "exit"

            # =====================
            # UPLOAD PROGRAM
            # =====================

            elif action == "upload_program":

                upload_program()

            # =====================
            # UPLOAD FILE
            # =====================

            elif action == "upload_file":

                upload_file()

            # =====================
            # START TRAIN
            # =====================

            elif action == "start_train":

                start_train()

            # =====================
            # OTA UPDATE
            # =====================

            elif action == "ota":

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

            elif action == "status":

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

            elif action == "nodes":

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

            elif action == "tasks":

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

        except Exception as e:

            print("Command error:", e)

            time.sleep(1)