import json
import time
import uuid
import threading
import sys

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
# MQTT RECOVERY
# =========================================================

def reconnect_mqtt():

    global mqtt_fail_count

    with reconnect_lock:

        try:

            print_event("Reconnecting MQTT...")

            client.loop_stop()

            client.disconnect()

        except:
            pass

        while True:

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

            except Exception as e:

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

        node = payload.get(
            "node"
        )

        status = payload.get(
            "status"
        )

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

add_task(
    DEFAULT_TASK.copy()
)


# =========================================================
# MAIN LOOP
# =========================================================

def coordinator_loop():

    print_event(
        "Coordinator started"
    )

    while service_running:

        try:

            check_node_health()

            time.sleep(
                TASK_DISPATCH_INTERVAL
            )

        except Exception:

            logger.exception(
                "Coordinator error"
            )

            time.sleep(2)