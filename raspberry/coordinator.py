import json
import time
import uuid
import threading

import paho.mqtt.client as mqtt

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


# =========================
# STATE
# =========================

ready_nodes = set()

node_list = []

node_index = 0

running_tasks = {}

completed_tasks = {}

node_last_seen = {}

service_running = True


# =========================
# DATABASE INIT
# =========================

init_db()


# =========================
# NODE MANAGEMENT
# =========================

def update_node_list():

    global node_list

    node_list = list(ready_nodes)


def get_next_node():

    global node_index

    if not node_list:
        return None

    if node_index >= len(node_list):

        node_index = 0

    node = node_list[node_index]

    node_index += 1

    return node


# =========================
# NODE HEALTH MONITOR
# =========================

def check_node_health():

    now = time.time()

    dead_nodes = []

    for node, last_seen in list(node_last_seen.items()):

        if now - last_seen > NODE_HEARTBEAT_TIMEOUT:

            dead_nodes.append(node)

    for node in dead_nodes:

        print("Node timeout:", node)

        ready_nodes.discard(node)

        node_last_seen.pop(node, None)

        update_node_list()


# =========================
# TASK MANAGEMENT
# =========================

def add_task(task):

    task_id = str(uuid.uuid4())

    task["task_id"] = task_id

    task["retry"] = 0

    task["created"] = time.time()

    insert_task(task)

    print("Task stored:", task_id)

    return task_id


def get_next_task():

    return get_pending_task()


def mark_running(task_id):

    if task_id in running_tasks:

        running_tasks[task_id]["start_time"] = time.time()

        print("Task running:", task_id)


def mark_completed(task_id, status):

    if task_id not in running_tasks:
        return

    task_info = running_tasks[task_id]

    task = task_info["task"]

    retry = task.get("retry", 0)

    print("Task completed:", task_id, status)

    if status in ["error", "timeout"]:

        if retry < RETRY_LIMIT:

            increment_retry(task)

            print(
                "Retry task:",
                task_id,
                "attempt",
                retry + 1
            )

        else:

            update_status(
                task_id,
                "failed"
            )

            print(
                "Task failed permanently:",
                task_id
            )

    else:

        update_status(
            task_id,
            status
        )

    completed_tasks[task_id] = status

    del running_tasks[task_id]


# =========================
# TIMEOUT MONITOR
# =========================

def check_timeouts():

    now = time.time()

    expired = []

    for task_id, info in list(running_tasks.items()):

        start = info["start_time"]

        if now - start > TASK_TIMEOUT:

            expired.append(task_id)

    for task_id in expired:

        print("Task timeout:", task_id)

        mark_completed(
            task_id,
            "timeout"
        )


# =========================
# MQTT CONNECT
# =========================

def on_connect(client, userdata, flags, rc):

    if rc == 0:

        print("Server connected")

        client.subscribe("cluster/status/+")
        client.subscribe("cluster/task_status/+")
        client.subscribe("cluster/result/+")
        client.subscribe("cluster/progress/+")

    else:

        print("MQTT connection failed:", rc)


# =========================
# MESSAGE HANDLER
# =========================

def on_message(client, userdata, msg):

    topic = msg.topic

    try:

        payload = json.loads(msg.payload)

    except Exception as e:

        print("JSON error:", e)

        return

    # NODE STATUS

    if topic.startswith("cluster/status"):

        node = payload.get("node")

        status = payload.get("status")

        if not node:
            return

        node_last_seen[node] = time.time()

        if status in ["ready", "online"]:

            ready_nodes.add(node)

            update_node_list()

            print("Node READY:", node)

        elif status == "offline":

            ready_nodes.discard(node)

            node_last_seen.pop(node, None)

            update_node_list()

            print("Node OFFLINE:", node)

    # TASK STATUS

    elif topic.startswith("cluster/task_status"):

        task_id = payload.get("task_id")

        status = payload.get("status")

        if not task_id:
            return

        print("Task status:", task_id, status)

        if status == "running":

            mark_running(task_id)

        if status in ["done", "error", "timeout"]:

            mark_completed(task_id, status)

    # PROGRESS

    elif topic.startswith("cluster/progress"):

        node = payload.get("node")

        stage = payload.get("stage", "unknown")

        progress = payload.get("progress", 0)

        print(
            "Progress:",
            node,
            stage,
            str(progress) + "%"
        )

        update_progress(
            node,
            stage,
            progress
        )

    # RESULT

    elif topic.startswith("cluster/result"):

        print("Result received")

        node = payload.get("node")

        result = payload.get("result")

        if not node or not result:

            print("Invalid result payload")

            return

        filename = result.get(
            "filename",
            "result.csv"
        )

        data = result.get("data")

        if not data:

            print("Result data kosong")

            return

        handle_result(
            node,
            filename,
            data
        )


# =========================
# MQTT SETUP
# =========================

client = mqtt.Client()

client.on_connect = on_connect

client.on_message = on_message

client.connect(
    MQTT_BROKER,
    1883,
    60
)

client.loop_start()


# =========================
# INITIAL TASK
# =========================

add_task(DEFAULT_TASK.copy())


# =========================
# DISPATCH TASK
# =========================

def dispatch_task():

    if not ready_nodes:
        return

    task = get_next_task()

    if not task:
        return

    node = get_next_node()

    if not node:
        return

    topic = "cluster/task/" + node

    try:

        client.publish(
            topic,
            json.dumps(task)
        )

        update_status(
            task["task_id"],
            "running"
        )

        running_tasks[task["task_id"]] = {

            "task": task,
            "start_time": time.time(),
            "node": node

        }

        print(
            "Task sent to",
            node,
            task["task_id"]
        )

        ready_nodes.discard(node)

        update_node_list()

    except Exception as e:

        print("Publish failed:", e)


# =========================
# MAIN LOOP
# =========================

def coordinator_loop():

    print("[COORDINATOR] Loop started")

    while service_running:

        try:

            dispatch_task()

            check_timeouts()

            check_node_health()

            time.sleep(
                TASK_DISPATCH_INTERVAL
            )

        except Exception as e:

            print(
                "[COORDINATOR ERROR]",
                e
            )

            time.sleep(2)


# =========================
# SERVICE ENTRYPOINT
# =========================

def start_coordinator():

    print("[SERVICE] Starting coordinator")

    thread = threading.Thread(
        target=coordinator_loop,
        daemon=True
    )

    thread.start()

    print("[SERVICE] Coordinator running")


# =========================
# OPTIONAL STOP SERVICE
# =========================

def stop_coordinator():

    global service_running

    service_running = False

    print("[SERVICE] Coordinator stopped")