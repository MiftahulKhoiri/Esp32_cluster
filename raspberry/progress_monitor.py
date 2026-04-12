import time
import threading


# =========================
# STATE
# =========================

node_progress = {}

lock = threading.Lock()


# =========================
# UPDATE
# =========================

def update_progress(
    node,
    payload
):

    with lock:

        node_progress[node] = {

            "stage": payload.get(
                "stage",
                "unknown"
            ),

            "progress": payload.get(
                "progress",
                0
            ),

            "memory_free_kb":
                payload.get(
                    "memory_free_kb"
                ),

            "memory_used_kb":
                payload.get(
                    "memory_used_kb"
                ),

            "cpu_percent":
                payload.get(
                    "cpu_percent"
                ),

            "flash_free_kb":
                payload.get(
                    "flash_free_kb"
                ),

            "flash_percent":
                payload.get(
                    "flash_percent"
                ),

            "temperature":
                payload.get(
                    "temperature"
                ),

            "time":
                time.strftime(
                    "%H:%M:%S"
                )

        }


# =========================
# PRINT
# =========================

def print_progress():

    with lock:

        print("")
        print(
            "===================================="
        )
        print(
            " NODE SYSTEM MONITOR"
        )
        print(
            "===================================="
        )
        print("")

        if not node_progress:

            print(
                "Belum ada data"
            )

            return

        for node, info in node_progress.items():

            print(node)

            print(
                "  stage      :",
                info["stage"]
            )

            print(
                "  progress   :",
                str(info["progress"]) + "%"
            )

            if info["memory_free_kb"] is not None:

                print(
                    "  RAM free   :",
                    info["memory_free_kb"],
                    "KB"
                )

                print(
                    "  RAM used   :",
                    info["memory_used_kb"],
                    "KB"
                )

            if info["cpu_percent"] is not None:

                print(
                    "  CPU        :",
                    str(info["cpu_percent"]) + "%"
                )

            if info["flash_percent"] is not None:

                print(
                    "  Flash free :",
                    info["flash_free_kb"],
                    "KB"
                )

                print(
                    "  Flash used :",
                    str(info["flash_percent"]) + "%"
                )

            if info["temperature"] is not None:

                print(
                    "  Temp       :",
                    str(info["temperature"]),
                    "C"
                )

            print(
                "  update     :",
                info["time"]
            )

            print("")