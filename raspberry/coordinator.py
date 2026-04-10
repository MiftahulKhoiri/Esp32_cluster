import json
import time
import uuid

import paho.mqtt.client as mqtt

from config import (
    MQTT_BROKER,
    TASK_DISPATCH_INTERVAL,
    DEFAULT_TASK,
    RETRY_LIMIT
)


# =========================
# STATE
# =========================

ready_nodes = set()

pending_tasks = []

running_tasks = {}

completed_tasks = {}

TASK_TIMEOUT = 30


# =========================
# TASK MANAGEMENT
# =========================

def add_task(task):

    task_id = str(uuid.uuid4())

    task["task_id"] = task_id

    task["retry"] = 0

    task["created"] = time.time()

    pending_tasks.append(task)

    print("Task added:", task_id)

    return task_id


def get_next_task():

    if not pending_tasks:
        return None

    return pending_tasks.pop(0)


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

    print(
        "Task completed:",
        task_id,
        status
    )

    # ---------------------
    # RETRY LOGIC
    # ---------------------

    if status in ["error", "timeout"]:

        if retry < RETRY_LIMIT:

            task["retry"] = retry + 1

            pending_tasks.append(task)

            print(
                "Retry task:",
                task_id,
                "attempt",
                task["retry"]
            )

        else:

            completed_tasks[task_id] = {

                "status": "failed",

                "retry": retry,

                "finished": time.time()

            }

            print(
                "Task failed permanently:",
                task_id
            )

    else:

        completed_tasks[task_id] = {

            "status": status,

            "retry": retry,

            "finished": time.time()

        }

    del running_tasks[task_id]


# =========================
# TIMEOUT MONITOR
# =========================

def check_timeouts():

    now = time.time()

    expired = []

    for task_id, info in running_tasks.items():

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

    print("Server connected")

    client.subscribe("cluster/status/+")
    client.subscribe("cluster/task_status/+")
    client.subscribe("cluster/result/+")


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

    # ---------------------
    # NODE STATUS
    # ---------------------

    if topic.startswith("cluster/status"):

        node = payload.get("node")

        status = payload.get("status")

        if not node:
            return

        if status == "ready":

            ready_nodes.add(node)

            print("Node READY:", node)

        elif status == "offline":

            ready_nodes.discard(node)

            print("Node OFFLINE:", node)

    # ---------------------
    # TASK STATUS (ACK)
    # ---------------------

    if topic.startswith("cluster/task_status"):

        task_id = payload.get("task_id")

        status = payload.get("status")

        if not task_id:
            return

        print(
            "Task status:",
            task_id,
            status
        )

        if status == "running":

            mark_running(task_id)

        if status in [

            "done",
            "error",
            "timeout"

        ]:

            mark_completed(
                task_id,
                status
            )

    # ---------------------
    # TASK RESULT
    # ---------------------

    if topic.startswith("cluster/result"):

        print("Result received")

        print(payload)


# =========================
# MQTT SETUP
# =========================

client = mqtt.Client()

client.on_connect = on_connect

client.on_message = on_message

client.connect(MQTT_BROKER)

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

    node = list(ready_nodes)[0]

    topic = "cluster/task/" + node

    try:

        client.publish(
            topic,
            json.dumps(task)
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

    except Exception as e:

        print("Publish failed:", e)

        pending_tasks.insert(0, task)


# =========================
# MAIN LOOP
# =========================

while True:

    dispatch_task()

    check_timeouts()

    time.sleep(
        TASK_DISPATCH_INTERVAL
    )