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

# =========================================================
# LOGGER
# =========================================================

logger = get_logger("coordinator")

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
# PROGRESS FILTER
# =========================================================

progress_milestones = {}

PROGRESS_STEP = 10


def should_log_progress(node, progress):

    last = progress_milestones.get(
        node,
        -10
    )

    if progress >= last + PROGRESS_STEP:

        progress_milestones[node] = progress

        return True

    return False


# =========================================================
# DATABASE INIT
# =========================================================

try:

    init_db()

    logger.info(
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
# NODE HEALTH MONITOR
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

                dead_nodes.append(
                    node
                )

        for node in dead_nodes:

            if node in ready_nodes:

                logger.warning(
                    "Node timeout",
                    extra={
                        "node": node
                    }
                )

                ready_nodes.discard(
                    node
                )

                node_last_seen.pop(
                    node,
                    None
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

    try:

        insert_task(task)

        logger.info(
            "Task stored",
            extra={
                "task_id": task_id,
                "type": task.get(
                    "type"
                )
            }
        )

        return task_id

    except Exception:

        logger.exception(
            "Failed to insert task"
        )

        raise


def get_next_task():

    try:

        return get_pending_task()

    except Exception:

        logger.exception(
            "Failed to fetch pending task"
        )

        return None


def mark_running(task_id):

    with state_lock:

        if task_id in running_tasks:

            running_tasks[
                task_id
            ]["start_time"] = time.time()

    logger.info(
        "Task running",
        extra={
            "task_id": task_id
        }
    )


def mark_completed(
    task_id,
    status
):

    with state_lock:

        if task_id not in running_tasks:

            return

        task_info = running_tasks[
            task_id
        ]

        task = task_info[
            "task"
        ]

        retry = task.get(
            "retry",
            0
        )

    logger.info(
        "Task completed",
        extra={
            "task_id": task_id,
            "status": status
        }
    )

    try:

        if status in [
            "error",
            "timeout"
        ]:

            if retry < RETRY_LIMIT:

                increment_retry(
                    task
                )

                logger.warning(
                    "Retry task",
                    extra={
                        "task_id": task_id,
                        "attempt": retry + 1
                    }
                )

            else:

                update_status(
                    task_id,
                    "failed"
                )

                logger.error(
                    "Task failed permanently",
                    extra={
                        "task_id": task_id
                    }
                )

        else:

            update_status(
                task_id,
                status
            )

    except Exception:

        logger.exception(
            "Failed updating task status"
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
# TIMEOUT MONITOR
# =========================================================

def check_timeouts():

    now = time.time()

    expired = []

    with state_lock:

        for task_id, info in list(
            running_tasks.items()
        ):

            start = info[
                "start_time"
            ]

            if now - start > \
               TASK_TIMEOUT:

                expired.append(
                    task_id
                )

    for task_id in expired:

        logger.error(
            "Task timeout",
            extra={
                "task_id": task_id
            }
        )

        mark_completed(
            task_id,
            "timeout"
        )


# =========================================================
# MQTT RECONNECT
# =========================================================

def ensure_mqtt_connection():

    try:

        if not client.is_connected():

            logger.warning(
                "MQTT disconnected, reconnecting"
            )

            client.reconnect()

    except Exception:

        try:

            client.connect(
                MQTT_BROKER,
                1883,
                60
            )

            logger.info(
                "MQTT reconnected"
            )

        except Exception:

            logger.exception(
                "MQTT reconnect failed"
            )


# =========================================================
# MQTT CONNECT
# =========================================================

def on_connect(
    client,
    userdata,
    flags,
    rc
):

    if rc == 0:

        logger.info(
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

    else:

        logger.error(
            "MQTT connection failed",
            extra={
                "rc": rc
            }
        )


# =========================================================
# MESSAGE HANDLER
# =========================================================

def on_message(
    client,
    userdata,
    msg
):

    topic = msg.topic

    try:

        payload = json.loads(
            msg.payload
        )

    except Exception:

        logger.exception(
            "Invalid JSON payload"
        )

        return

    # =====================
    # NODE STATUS
    # =====================

    if topic.startswith(
        "cluster/status"
    ):

        node = payload.get(
            "node"
        )

        status = payload.get(
            "status"
        )

        if not node:

            return

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

                    logger.info(
                        "Node ready",
                        extra={
                            "node": node
                        }
                    )

            elif status == \
                 "offline":

                if node in ready_nodes:

                    ready_nodes.discard(
                        node
                    )

                    node_last_seen.pop(
                        node,
                        None
                    )

                    logger.warning(
                        "Node offline",
                        extra={
                            "node": node
                        }
                    )

        update_node_list()

    # =====================
    # TASK STATUS
    # =====================

    elif topic.startswith(
        "cluster/task_status"
    ):

        task_id = payload.get(
            "task_id"
        )

        status = payload.get(
            "status"
        )

        if not task_id:

            return

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

    # =====================
    # PROGRESS
    # =====================

    elif topic.startswith(
        "cluster/progress"
    ):

        node = payload.get(
            "node"
        )

        if not node:

            return

        stage = payload.get(
            "stage",
            "unknown"
        )

        progress = payload.get(
            "progress",
            0
        )

        if should_log_progress(
            node,
            progress
        ):

            logger.info(
                "Progress",
                extra={
                    "node": node,
                    "stage": stage,
                    "progress": progress
                }
            )

        update_progress(
            node,
            payload
        )

    # =====================
    # RESULT
    # =====================

    elif topic.startswith(
        "cluster/result"
    ):

        logger.info(
            "Result received"
        )

        try:

            node = payload.get(
                "node"
            )

            result = payload.get(
                "result"
            )

            if not node or \
               not result:

                logger.warning(
                    "Invalid result payload"
                )

                return

            filename = result.get(
                "filename",
                "result.csv"
            )

            data = result.get(
                "data"
            )

            if not data:

                logger.warning(
                    "Empty result data"
                )

                return

            handle_result(
                node,
                filename,
                data
            )

            logger.info(
                "Result stored",
                extra={
                    "node": node,
                    "file": filename
                }
            )

        except Exception:

            logger.exception(
                "Result handling failed"
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
# DISPATCH TASK
# =========================================================

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

        with state_lock:

            running_tasks[
                task["task_id"]
            ] = {

                "task": task,
                "start_time":
                    time.time(),
                "node": node

            }

            ready_nodes.discard(
                node
            )

            progress_milestones.pop(
                node,
                None
            )

        update_node_list()

        logger.info(
            "Task dispatched",
            extra={
                "task_id":
                    task["task_id"],
                "node": node
            }
        )

    except Exception:

        logger.exception(
            "Failed to dispatch task"
        )


# =========================================================
# MAIN LOOP
# =========================================================

def coordinator_loop():

    logger.info(
        "Coordinator loop started"
    )

    while service_running:

        try:

            ensure_mqtt_connection()

            dispatch_task()

            check_timeouts()

            check_node_health()

            time.sleep(
                TASK_DISPATCH_INTERVAL
            )

        except Exception:

            logger.exception(
                "Coordinator loop error"
            )

            time.sleep(2)


# =========================================================
# SERVICE ENTRYPOINT
# =========================================================

def start_coordinator():

    logger.info(
        "Starting coordinator service"
    )

    thread = threading.Thread(
        target=coordinator_loop,
        daemon=True
    )

    thread.start()

    logger.info(
        "Coordinator running"
    )


# =========================================================
# STOP SERVICE
# =========================================================

def stop_coordinator():

    global service_running

    service_running = False

    logger.warning(
        "Coordinator stopped"
    )