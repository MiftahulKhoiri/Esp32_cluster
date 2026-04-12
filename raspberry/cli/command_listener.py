# raspberry/cli/command_listener.py

import time

from raspberry.cli.upload_handler import handle_upload


def command_listener(services_running):

    while services_running():

        try:

            cmd = input("> ").strip().lower()

            # EXIT

            if cmd == "exit":

                return "exit"

            # UPLOAD

            elif cmd == "upload":

                handle_upload()

            # STATUS

            elif cmd == "status":

                from raspberry.coordinator import ready_nodes

                print("")
                print("Ready nodes:")
                print(ready_nodes)
                print("")

            # NODES

            elif cmd == "nodes":

                from raspberry.coordinator import node_last_seen

                print("")
                print("Nodes:")

                if not node_last_seen:

                    print("  (no nodes connected)")

                for node in node_last_seen:

                    print("  -", node)

                print("")

            # TASKS

            elif cmd == "tasks":

                from raspberry.coordinator import running_tasks

                print("")
                print("Running tasks:")

                if not running_tasks:

                    print("  (no running tasks)")

                for task_id in running_tasks:

                    print("  -", task_id)

                print("")

            elif cmd == "":

                continue

            else:

                print("Unknown command")

        except Exception as e:

            print("Command error:", e)

            time.sleep(1)