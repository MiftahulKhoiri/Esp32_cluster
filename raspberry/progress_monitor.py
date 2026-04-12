import time
import threading


# =========================
# GLOBAL STATE
# =========================

node_progress = {}

lock = threading.Lock()


# =========================
# UPDATE PROGRESS
# =========================

def update_progress(
    node,
    stage,
    progress
):

    with lock:

        node_progress[node] = {

            "stage": stage,
            "progress": progress,
            "time": time.strftime(
                "%H:%M:%S"
            )

        }


# =========================
# PRINT PROGRESS
# =========================

def print_progress():

    with lock:

        print("")
        print(
            "=============================="
        )
        print(
            " NODE PROGRESS MONITOR"
        )
        print(
            "=============================="
        )
        print("")

        if not node_progress:

            print(
                "Belum ada progress"
            )

        for node, info in node_progress.items():

            print(node)

            print(
                "  stage    :",
                info["stage"]
            )

            print(
                "  progress :",
                str(info["progress"]) + "%"
            )

            print(
                "  update   :",
                info["time"]
            )

            print("")


# =========================
# RESET
# =========================

def reset_progress():

    with lock:

        node_progress.clear()