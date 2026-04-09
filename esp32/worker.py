import time
import random

try:
    import led
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False


# =========================
# MAIN ENTRY
# =========================

def run_task(data):

    try:

        if LED_AVAILABLE:
            led.set_state(led.STATE_RUNNING)

        if not isinstance(data, dict):

            return error_result("Invalid task format")

        task_type = data.get("task")

        if task_type is None:

            return error_result("Missing task field")

        if task_type == "random":

            return task_random(data)

        elif task_type == "sum":

            return task_sum(data)

        elif task_type == "status":

            return task_status()

        else:

            return error_result(
                "Unknown task: {}".format(task_type)
            )

    except Exception as e:

        return error_result(str(e))

    finally:

        if LED_AVAILABLE:
            led.set_state(led.STATE_MQTT)


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

    return success_result(result)


# =========================
# TASK: SUM NUMBERS
# =========================

def task_sum(data):

    numbers = data.get("numbers", [])

    if not isinstance(numbers, list):

        return error_result("numbers must be list")

    total = 0

    for n in numbers:

        total += n

    return success_result(total)


# =========================
# TASK: NODE STATUS
# =========================

def task_status():

    uptime = time.ticks_ms() // 1000

    return success_result({

        "uptime_seconds": uptime
    })


# =========================
# RESPONSE HELPERS
# =========================

def success_result(result):

    return {

        "status": "ok",
        "result": result

    }


def error_result(message):

    return {

        "status": "error",
        "message": message

    }