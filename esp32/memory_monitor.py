import gc
import time

try:
    import ujson
    from config import NODE_ID
    from main import client
except:
    client = None


# =========================
# CONFIG
# =========================

MEMORY_INTERVAL = 15      # seconds
MEMORY_WARNING_KB = 40    # warning threshold
MEMORY_CRITICAL_KB = 20   # reset threshold


last_report = 0


# =========================
# GET MEMORY INFO
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
# SEND MEMORY STATUS
# =========================

def send_memory_status():

    global last_report

    now = time.time()

    if now - last_report < MEMORY_INTERVAL:
        return

    last_report = now

    try:

        info = get_memory_info()

        payload = {

            "node": NODE_ID,
            "stage": "memory",
            "progress": info["percent"],
            "free_kb": info["free_kb"],
            "used_kb": info["used_kb"]

        }

        if client:

            client.publish(

                "cluster/progress/" + NODE_ID,

                ujson.dumps(payload)

            )

        print(

            "MEMORY:",
            info["free_kb"],
            "KB free"
        )

        # WARNING

        if info["free_kb"] < MEMORY_WARNING_KB:

            print(
                "WARNING: Low memory"
            )

        # CRITICAL

        if info["free_kb"] < MEMORY_CRITICAL_KB:

            print(
                "CRITICAL: Memory exhausted"
            )

            import machine

            machine.reset()

    except Exception as e:

        print(
            "Memory monitor error:",
            e
        )