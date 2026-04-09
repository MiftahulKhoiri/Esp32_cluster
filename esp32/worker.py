import time
import random

try:
    import led
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False


# =========================
# CONFIG
# =========================

DEFAULT_TIMEOUT = 10


# =========================
# MAIN ENTRY
# =========================

def run_task(data):

    start_time = time.time()

    try:

        if LED_AVAILABLE:
            led.set_state(led.STATE_RUNNING)

        if not isinstance(data, dict):

            return error_result(
                task_id="unknown",
                message="Invalid task format"
            )

        task_id = data.get(
            "task_id",
            generate_task_id()
        )

        timeout = int(
            data.get(
                "timeout",
                DEFAULT_TIMEOUT
            )
        )

        task_type = data.get("task")

        if task_type is None:

            return error_result(
                task_id,
                "Missing task field"
            )

        # =====================
        # DISPATCH
        # =====================

        if task_type == "random":

            result = task_random(data)

        elif task_type == "sum":

            result = task_sum(data)

        elif task_type == "status":

            result = task_status()

        else:

            return error_result(
                task_id,
                "Unknown task: {}".format(task_type)
            )

        # =====================
        # TIMEOUT CHECK
        # =====================

        duration = time.time() - start_time

        if duration > timeout:

            return timeout_result(
                task_id,
                duration
            )

        return success_result(
            task_id,
            result,
            duration
        )

    except Exception as e:

        return error_result(
            task_id,
            str(e)
        )

    finally:

        if LED_AVAILABLE:
            led.set_state(led.STATE_READY)


# =========================
# TASK: RANDOM NUMBER
# =========================

def task_random(data):

    count = int(data.get("count", 10))

    if count <= 0:
        count = 1

    result = []

    for _ in range(count):

        number = random.randint(1, 6)

        result.append(number)

    return result


# =========================
# TASK: SUM NUMBERS
# =========================

def task_sum(data):

    numbers = data.get("numbers", [])

    if not isinstance(numbers, list):

        raise ValueError(
            "numbers must be list"
        )

    total = 0

    for n in numbers:

        total += n

    return total


# =========================
# TASK: NODE STATUS
# =========================

def task_status():

    uptime = time.ticks_ms() // 1000

    return {

        "uptime_seconds": uptime
    }


# =========================
# RESPONSE HELPERS
# =========================

def success_result(task_id, result, duration):

    return {

        "task_id": task_id,

        "status": "done",

        "duration": duration,

        "result": result

    }


def timeout_result(task_id, duration):

    return {

        "task_id": task_id,

        "status": "timeout",

        "duration": duration

    }


def error_result(task_id, message):

    return {

        "task_id": task_id,

        "status": "error",

        "message": message

    }


# =========================
# TASK ID GENERATOR
# =========================

def generate_task_id():

    return "local_" + str(
        time.ticks_ms()
    )