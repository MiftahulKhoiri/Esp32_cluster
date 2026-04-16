import gc
import time
import os
import machine
import ujson

from config import NODE_ID


# =========================
# CONFIG
# =========================

MONITOR_INTERVAL = 15      # seconds

MEMORY_WARNING_KB = 40
MEMORY_CRITICAL_KB = 20

CPU_SAMPLE_TIME = 0.2      # seconds


last_report = 0


# =========================
# MEMORY
# =========================

def get_memory_info():

    gc.collect()

    free = gc.mem_free()
    alloc = gc.mem_alloc()

    total = free + alloc

    free_kb = free // 1024
    used_kb = alloc // 1024

    percent = int(
        (alloc / total) * 100
    )

    return {

        "free_kb": free_kb,
        "used_kb": used_kb,
        "percent": percent

    }


# =========================
# CPU USAGE (approx)
# =========================

def get_cpu_usage():

    start = time.ticks_ms()

    busy = 0

    end_time = start + int(
        CPU_SAMPLE_TIME * 1000
    )

    while time.ticks_ms() < end_time:

        busy += 1

    elapsed = time.ticks_diff(
        time.ticks_ms(),
        start
    )

    percent = int(

        (busy / (elapsed * 10)) * 100

    )

    if percent > 100:
        percent = 100

    return percent


# =========================
# FLASH STORAGE
# =========================

def get_flash_usage():

    try:

        stat = os.statvfs("/")

        block_size = stat[0]

        total_blocks = stat[2]
        free_blocks = stat[3]

        total = block_size * total_blocks
        free = block_size * free_blocks

        used = total - free

        total_kb = total // 1024
        free_kb = free // 1024

        percent = int(
            (used / total) * 100
        )

        return {

            "total_kb": total_kb,
            "free_kb": free_kb,
            "percent": percent

        }

    except Exception:

        return {

            "total_kb": 0,
            "free_kb": 0,
            "percent": 0

        }


# =========================
# TEMPERATURE
# =========================

def get_temperature():

    try:

        temp = machine.temperature()

        return int(temp)

    except Exception:

        return -1


# =========================
# SYSTEM STATUS
# =========================

def get_system_status():

    mem = get_memory_info()

    cpu = get_cpu_usage()

    flash = get_flash_usage()

    temp = get_temperature()

    return {

        "memory_free_kb": mem["free_kb"],
        "memory_used_kb": mem["used_kb"],
        "memory_percent": mem["percent"],

        "cpu_percent": cpu,

        "flash_total_kb": flash["total_kb"],
        "flash_free_kb": flash["free_kb"],
        "flash_percent": flash["percent"],

        "temperature": temp

    }


# =========================
# SEND STATUS
# =========================

def send_system_status(client):

    global last_report

    now = time.time()

    if now - last_report < MONITOR_INTERVAL:
        return

    last_report = now

    try:

        status = get_system_status()

        payload = {

            "node": NODE_ID,
            "stage": "system",

            "progress": status["memory_percent"],

            "memory_free_kb": status[
                "memory_free_kb"
            ],

            "memory_used_kb": status[
                "memory_used_kb"
            ],

            "cpu_percent": status[
                "cpu_percent"
            ],

            "flash_free_kb": status[
                "flash_free_kb"
            ],

            "flash_percent": status[
                "flash_percent"
            ],

            "temperature": status[
                "temperature"
            ]

        }

        # publish only if client exists

        if client is not None:

            client.publish(

                "cluster/progress/" + NODE_ID,

                ujson.dumps(payload)

            )

        print(

            "SYSTEM:",
            payload

        )

        # =====================
        # WARNING
        # =====================

        if status["memory_free_kb"] < MEMORY_WARNING_KB:

            print(

                "WARNING: Low memory"

            )

        # =====================
        # CRITICAL RESET
        # =====================

        if status["memory_free_kb"] < MEMORY_CRITICAL_KB:

            print(

                "CRITICAL: Memory exhausted"

            )

            machine.reset()

    except Exception as e:

        print(

            "System monitor error:",
            e

        )