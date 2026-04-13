import time
import threading

from toolsupdate.logger import get_logger

log = get_logger("PROGRESS")

# =========================
# STATE
# =========================

node_progress = {}

last_printed = {}

lock = threading.Lock()

PROGRESS_STEP = 10


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
# CHANGE DETECTION
# =========================

def should_print(
    node,
    info
):

    last = last_printed.get(node)

    if last is None:

        last_printed[node] = info

        return True

    # progress milestone
    if info["progress"] >= \
       last["progress"] + PROGRESS_STEP:

        last_printed[node] = info

        return True

    # stage change
    if info["stage"] != last["stage"]:

        last_printed[node] = info

        return True

    # cpu change
    if info["cpu_percent"] != \
       last["cpu_percent"]:

        last_printed[node] = info

        return True

    # temperature change
    if info["temperature"] != \
       last["temperature"]:

        last_printed[node] = info

        return True

    return False


# =========================
# PRINT EVENT
# =========================

def print_progress():

    with lock:

        if not node_progress:

            return

        for node, info in node_progress.items():

            if not should_print(
                node,
                info
            ):
                continue

            log.info(
                "Node update",
                extra={
                    "node": node,
                    "stage": info["stage"],
                    "progress": info["progress"],
                    "cpu": info["cpu_percent"],
                    "temp": info["temperature"]
                }
            )