import json
import time
import uuid
import threading
import sys
import os
import signal

import paho.mqtt.client as mqtt

from toolsupdate.logger import get_logger

from raspberry.config import (
    MQTT_BROKER,
    TASK_DISPATCH_INTERVAL,
    DEFAULT_TASK,
    RETRY_LIMIT,
    TASK_TIMEOUT,
    NODE_HEARTBEAT_TIMEOUT
)

from raspberry.database import (
    init_db,
    insert_task,
    get_pending_task,
    update_status,
    increment_retry
)

from raspberry.result_handler import (
    handle_result
)

from raspberry.progress_monitor import (
    update_progress
)

logger = get_logger("coordinator")

# =========================================================
# MQTT RECOVERY CONFIG
# =========================================================

mqtt_fail_count = 0
MAX_MQTT_FAIL = 5

reconnect_lock = threading.Lock()

# =========================================================
# SERVICE WATCHDOG
# =========================================================

last_loop_time = time.time()
WATCHDOG_TIMEOUT = 120

# =========================================================
# SIMPLE CONSOLE OUTPUT
# =========================================================

def print_event(message):
    print(message)


last_progress = {}
PROGRESS_STEP = 10


def print_progress(node, progress):

    last = last_progress.get(node)

    if last is None or progress >= last + PROGRESS_STEP:

        last_progress[node] = progress

        print(
            f"Progress {node}: {progress}%"
        )


# =========================================================
# STATE
# =========================================================

state_lock = threading.Lock()

ready_nodes = set()
node_list = []
node_index = 0

running_tasks = {}
completed_tasks = {}

node_last_seen = {}

service_running = True
shutdown_requested = False


# =========================================================
# DATABASE
# =========================================================

init_db()

print_event(
    "Database initialized"
)


# =========================================================
# NODE MANAGEMENT
# =========================================================

def update_node_list():

    global node_list

    with state_lock:

        node_list = list(
            ready_nodes
        )


def get_next_node():

    global node_index

    with state_lock:

        if not node_list:
            return None

        if node_index >= len(node_list):
            node_index = 0

        node = node_list[node_index]

        node_index += 1

        return node


# =========================================================
# NODE HEALTH
# =========================================================

def check_node_health():

    now = time.time()

    dead_nodes = []

    with state_lock:

        for node, last_seen in list(
            node_last_seen.items()
        ):

            if now - last_seen > \
               NODE_HEARTBEAT_TIMEOUT:

                dead_nodes.append(node)

        for node in dead_nodes:

            if node in ready_nodes:

                ready_nodes.discard(node)

                node_last_seen.pop(
                    node,
                    None
                )

                print_event(
                    f"Node timeout: {node}"
                )

    if dead_nodes:

        update_node_list()


# =========================================================
# TASK TIMEOUT
# =========================================================

def check_timeouts():

    now = time.time()

    timed_out = []

    with state_lock:

        for task_id, info in list(
            running_tasks.items()
        ):

            start_time = info.get(
                "start_time"
            )

            if not start_time:
                continue

            if now - start_time > TASK_TIMEOUT:

                timed_out.append(
                    task_id
                )

    for task_id in timed_out:

        print_event(
            f"Task timeout: {task_id}"
        )

        update_status(
            task_id,
            "timeout"
        )


# =========================================================
# SERVICE WATCHDOG
# =========================================================

def watchdog_monitor():

    global last_loop_time

    while service_running:

        try:

            now = time.time()

            if now - last_loop_time > WATCHDOG_TIMEOUT:

                print_event(
                    "Watchdog timeout — restarting service"
                )

                time.sleep(2)

                os.execv(
                    sys.executable,
                    [sys.executable] + sys.argv
                )

            time.sleep(10)

        except Exception:

            logger.exception(
                "Watchdog error"
            )


# =========================================================
# MQTT RECOVERY
# =========================================================

def reconnect_mqtt():

    global mqtt_fail_count

    if shutdown_requested:
        return

    with reconnect_lock:

        try:

            print_event("Reconnecting MQTT...")

            client.loop_stop()

            client.disconnect()

        except:
            pass

        while not shutdown_requested:

            try:

                client.connect(
                    MQTT_BROKER,
                    1883,
                    60
                )

                client.loop_start()

                mqtt_fail_count = 0

                print_event(
                    "MQTT reconnected"
                )

                return

            except Exception:

                mqtt_fail_count += 1

                print_event(
                    f"MQTT reconnect failed: {mqtt_fail_count}"
                )

                if mqtt_fail_count >= MAX_MQTT_FAIL:

                    print_event(
                        "Too many MQTT failures — restarting process"
                    )

                    time.sleep(2)

                    os.execv(
                        sys.executable,
                        [sys.executable] + sys.argv
                    )

                time.sleep(5)


# =========================================================
# GRACEFUL SHUTDOWN
# =========================================================

def shutdown_handler(signum, frame):

    global service_running
    global shutdown_requested

    if shutdown_requested:
        return

    shutdown_requested = True

    print_event(
        f"Shutdown signal received: {signum}"
    )

    service_running = False

    try:

        client.loop_stop()
    except:
        pass

    try:
        client.disconnect()
    except:
        pass

    print_event(
        "Shutdown complete"
    )

    sys.exit(0)


# =========================================================
# SAFE SIGNAL REGISTER
# =========================================================

try:

    if threading.current_thread() is threading.main_thread():

        signal.signal(
            signal.SIGINT,
            shutdown_handler
        )

        signal.signal(
            signal.SIGTERM,
            shutdown_handler
        )

except Exception:

    print_event(
        "Signal handler skipped"
    )


# =========================================================
# MQTT CALLBACK
# =========================================================

def on_connect(client, userdata, flags, rc):

    if rc == 0:

        print_event(
            "MQTT connected"
        )

        client.subscribe(
            "cluster/status/+"
        )

        client.subscribe(
            "cluster/task_status/+"
        )

        client.subscribe(
            "cluster/result/+"
        )

        client.subscribe(
            "cluster/progress/+"
        )


def on_disconnect(client, userdata, rc):

    print_event(
        f"MQTT disconnected: {rc}"
    )

    reconnect_mqtt()


def on_message(client, userdata, msg):

    topic = msg.topic

    payload = json.loads(
        msg.payload
    )

    if topic.startswith(
        "cluster/status"
    ):

        node = payload.get("node")

        status = payload.get("status")

        with state_lock:

            node_last_seen[node] = time.time()

            if status in ["ready", "online"]:

                if node not in ready_nodes:

                    ready_nodes.add(node)

                    print_event(
                        f"Node ready: {node}"
                    )

            elif status == "offline":

                if node in ready_nodes:

                    ready_nodes.discard(node)

                    print_event(
                        f"Node offline: {node}"
                    )

        update_node_list()

    elif topic.startswith(
        "cluster/progress"
    ):

        node = payload.get("node")

        progress = payload.get(
            "progress",
            0
        )

        print_progress(
            node,
            progress
        )

        update_progress(
            node,
            payload
        )

    elif topic.startswith(
        "cluster/result"
    ):

        result = payload.get(
            "result"
        )

        filename = result.get(
            "filename"
        )

        handle_result(
            payload.get("node"),
            filename,
            result.get("data")
        )

        print_event(
            f"Result stored: {filename}"
        )


# =========================================================
# MQTT SETUP
# =========================================================

client = mqtt.Client()

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.connect(
    MQTT_BROKER,
    1883,
    60
)

client.loop_start()


# =========================================================
# INITIAL TASK
# =========================================================

def add_task(task):

    task_id = str(
        uuid.uuid4()
    )

    task["task_id"] = task_id

    insert_task(task)

    print_event(
        f"Task added: {task_id}"
    )


add_task(
    DEFAULT_TASK.copy()
)


# =========================================================
# MAIN LOOP
# =========================================================

def coordinator_loop():

    global last_loop_time

    print_event(
        "Coordinator started"
    )

    while service_running:

        try:

            last_loop_time = time.time()

            check_node_health()

            check_timeouts()

            time.sleep(
                TASK_DISPATCH_INTERVAL
            )

        except Exception:

            logger.exception(
                "Coordinator error"
            )

            time.sleep(2)


# =========================================================
# START THREADS
# =========================================================

watchdog_thread = threading.Thread(
    target=watchdog_monitor,
    daemon=True
)

watchdog_thread.start()

coordinator_thread = threading.Thread(
    target=coordinator_loop,
    daemon=True
)

coordinator_thread.start()