import json
import time
import uuid
import threading

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

try:

    init_db()

    print_event(
        "Database initialized"
    )

except Exception:

    logger.exception(
        "Database initialization failed"
    )

    raise


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
# TASK MANAGEMENT
# =========================================================

def add_task(task):

    task_id = str(
        uuid.uuid4()
    )

    task["task_id"] = task_id
    task["retry"] = 0
    task["created"] = time.time()

    insert_task(task)

    print_event(
        f"Task stored: {task_id}"
    )

    return task_id


def get_next_task():

    try:

        return get_pending_task()

    except Exception:

        logger.exception(
            "Failed to fetch task"
        )

        return None


def mark_running(task_id):

    with state_lock:

        if task_id in running_tasks:

            running_tasks[
                task_id
            ]["start_time"] = time.time()

    print_event(
        f"Task started: {task_id}"
    )


def mark_completed(task_id, status):

    with state_lock:

        if task_id not in running_tasks:
            return

        task_info = running_tasks[
            task_id
        ]

        task = task_info["task"]

        retry = task.get(
            "retry",
            0
        )

    if status in [
        "error",
        "timeout"
    ]:

        if retry < RETRY_LIMIT:

            increment_retry(task)

            print_event(
                f"Retry task: {task_id}"
            )

        else:

            update_status(
                task_id,
                "failed"
            )

            print_event(
                f"Task failed: {task_id}"
            )

    else:

        update_status(
            task_id,
            status
        )

        print_event(
            f"Task finished: {task_id} {status}"
        )

    with state_lock:

        completed_tasks[
            task_id
        ] = status

        running_tasks.pop(
            task_id,
            None
        )


# =========================================================
# MQTT
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

            node_last_seen[
                node
            ] = time.time()

            if status in [
                "ready",
                "online"
            ]:

                if node not in ready_nodes:

                    ready_nodes.add(
                        node
                    )

                    print_event(
                        f"Node ready: {node}"
                    )

            elif status == "offline":

                if node in ready_nodes:

                    ready_nodes.discard(
                        node
                    )

                    print_event(
                        f"Node offline: {node}"
                    )

        update_node_list()

    elif topic.startswith(
        "cluster/task_status"
    ):

        task_id = payload.get(
            "task_id"
        )

        status = payload.get(
            "status"
        )

        if status == "running":

            mark_running(
                task_id
            )

        if status in [

            "done",
            "error",
            "timeout"

        ]:

            mark_completed(
                task_id,
                status
            )

    elif topic.startswith(
        "cluster/progress"
    ):

        node = payload.get(
            "node"
        )

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

            dispatch_task()

            check_timeouts()

            check_node_health()

            time.sleep(
                TASK_DISPATCH_INTERVAL
            )

        except Exception:

            logger.exception(
                "Coordinator error"
            )

            time.sleep(2)