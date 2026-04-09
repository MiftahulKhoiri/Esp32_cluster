import json
import time
import uuid

import paho.mqtt.client as mqtt

from config import (
    MQTT_BROKER,
    TASK_DISPATCH_INTERVAL,
    DEFAULT_TASK
)


# =========================
# STATE
# =========================

ready_nodes = set()

pending_tasks = []

running_tasks = {}

completed_tasks = {}


# =========================
# TASK MANAGEMENT
# =========================

def add_task(task):

    task_id = str(uuid.uuid4())

    task["task_id"] = task_id

    pending_tasks.append(task)

    print("Task added:", task_id)

    return task_id


def get_next_task():

    if not pending_tasks:

        return None

    return pending_tasks.pop(0)


def mark_running(task_id):

    running_tasks[task_id] = {

        "start_time": time.time()

    }


def mark_completed(task_id, status):

    if task_id in running_tasks:

        completed_tasks[task_id] = status

        del running_tasks[task_id]

        print(

            "Task completed:",
            task_id,
            status

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

    payload = json.loads(msg.payload)

    # ---------------------
    # NODE STATUS
    # ---------------------

    if topic.startswith("cluster/status"):

        node = payload["node"]

        status = payload["status"]

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

        task_id = payload["task_id"]

        status = payload["status"]

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
# MAIN LOOP
# =========================

while True:

    if ready_nodes:

        node = list(ready_nodes)[0]

        task = get_next_task()

        if task:

            topic = "cluster/task/" + node

            client.publish(

                topic,

                json.dumps(task)

            )

            print(

                "Task sent to",
                node,
                task["task_id"]

            )

            ready_nodes.discard(node)

    time.sleep(
        TASK_DISPATCH_INTERVAL
    )