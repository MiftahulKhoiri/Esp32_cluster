import time
import os
import sys
import ujson
import machine
import gc

# =========================
# BASE64 COMPAT
# =========================

try:
    import ubinascii as _b64

    def b64decode(data):
        return _b64.a2b_base64(data)

except ImportError:
    import base64 as _b64

    def b64decode(data):
        return _b64.b64decode(data)


try:
    import led
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False


# =========================
# CONFIG
# =========================

PROGRAM_DIR = "programs"
DATA_DIR = "data"

DEFAULT_TIMEOUT = 10
TRAINING_TIMEOUT = 300   # seconds


# =========================
# INIT DIRECTORIES
# =========================

def init_directories():

    if PROGRAM_DIR not in os.listdir():
        os.mkdir(PROGRAM_DIR)

    if DATA_DIR not in os.listdir():
        os.mkdir(DATA_DIR)


# =========================
# PROGRESS
# =========================

def send_progress(stage, percent):

    try:

        from config import NODE_ID
        from main import client

        payload = {

            "node": NODE_ID,
            "stage": stage,
            "progress": percent

        }

        client.publish(
            "cluster/progress/" + NODE_ID,
            ujson.dumps(payload)
        )

    except Exception as e:

        print("Progress error:", e)


# =========================
# MODULE RELOAD
# =========================

def reload_module(module_name):

    if module_name in sys.modules:

        print("Reloading:", module_name)

        del sys.modules[module_name]

        gc.collect()


# =========================
# RESUME META
# =========================

def get_meta_filename(filename):

    return filename + ".meta"


def get_meta_path(filename):

    return DATA_DIR + "/" + get_meta_filename(filename)


def load_last_chunk(filename):

    meta_file = get_meta_filename(filename)

    if meta_file not in os.listdir(DATA_DIR):
        return 0

    path = get_meta_path(filename)

    try:

        with open(path, "r") as f:

            meta = ujson.loads(f.read())

            return meta.get("last_chunk", 0)

    except Exception as e:

        print("Meta load error:", e)

        return 0


def save_last_chunk(filename, chunk):

    path = get_meta_path(filename)

    try:

        with open(path, "w") as f:

            f.write(
                ujson.dumps({
                    "last_chunk": chunk
                })
            )

    except Exception as e:

        print("Meta save error:", e)


def clear_meta(filename):

    meta_file = get_meta_filename(filename)

    try:

        if meta_file in os.listdir(DATA_DIR):

            os.remove(
                get_meta_path(filename)
            )

    except Exception as e:

        print("Meta clear error:", e)


# =========================
# WATCHDOG
# =========================

def start_watchdog():

    try:

        timeout_ms = TRAINING_TIMEOUT * 1000

        wdt = machine.WDT(
            timeout=timeout_ms
        )

        return wdt

    except Exception:

        print(
            "WDT fallback to 120s"
        )

        return machine.WDT(
            timeout=120000
        )


# =========================
# MAIN TASK
# =========================

def run_task(data):

    init_directories()

    try:

        if LED_AVAILABLE:
            led.set_state(
                led.STATE_RUNNING
            )

        task_type = data.get("type")

        if task_type == "upload_program":

            return handle_upload_program(data)

        elif task_type == "upload_chunk":

            return handle_upload_chunk(data)

        elif task_type == "train":

            return handle_training(data)

        else:

            return {

                "status": "error",
                "message": "Unknown task"

            }

    except Exception as e:

        print("Task error:", e)

        return {

            "status": "error",
            "message": str(e)

        }

    finally:

        if LED_AVAILABLE:
            led.set_state(
                led.STATE_READY
            )


# =========================
# UPLOAD PROGRAM
# =========================

def handle_upload_program(task):

    filename = task.get("filename")

    data_base64 = task.get("data")

    send_progress(
        "upload_program",
        0
    )

    path = PROGRAM_DIR + "/" + filename

    try:

        data = b64decode(data_base64)

    except Exception as e:

        print("Decode error:", e)

        return {

            "status": "error",
            "message": "decode failed"

        }

    with open(path, "wb") as f:

        f.write(data)

    module_name = filename.replace(
        ".py",
        ""
    )

    reload_module(module_name)

    send_progress(
        "upload_program",
        100
    )

    print("Program saved:", filename)

    return {

        "status": "program_updated"

    }


# =========================
# UPLOAD CHUNK
# =========================

def handle_upload_chunk(task):

    filename = task.get("filename")

    chunk_index = task.get(
        "chunk_index"
    )

    total_chunks = task.get(
        "total_chunks"
    )

    auto_train = task.get(
        "auto_train",
        False
    )

    last_chunk = load_last_chunk(
        filename
    )

    if chunk_index <= last_chunk:

        print(
            "Skip chunk",
            chunk_index
        )

        return {

            "status": "skip"

        }

    try:

        data = b64decode(
            task.get("data")
        )

    except Exception as e:

        print("Decode error:", e)

        return {

            "status": "error"

        }

    path = DATA_DIR + "/" + filename

    mode = "ab"

    if chunk_index == 1:
        mode = "wb"

    with open(path, mode) as f:

        f.write(data)

    save_last_chunk(
        filename,
        chunk_index
    )

    percent = int(
        (chunk_index / total_chunks) * 100
    )

    send_progress(
        "upload",
        percent
    )

    print(
        "Chunk",
        chunk_index,
        "/",
        total_chunks
    )

    if chunk_index == total_chunks:

        clear_meta(filename)

        print("File complete")

        if auto_train:

            return handle_training({

                "program": "train_model.py"

            })

    return {

        "status": "chunk_received"

    }


# =========================
# TRAINING
# =========================

def handle_training(task):

    program = task.get(
        "program",
        "train_model.py"
    )

    module_name = program.replace(
        ".py",
        ""
    )

    if PROGRAM_DIR not in sys.path:

        sys.path.append(
            PROGRAM_DIR
        )

    reload_module(
        module_name
    )

    wdt = start_watchdog()

    send_progress(
        "training",
        10
    )

    try:

        module = __import__(
            module_name
        )

        send_progress(
            "training",
            40
        )

        start_time = time.time()

        wdt.feed()

        result = module.run()

        duration = time.time() - start_time

        send_progress(
            "training",
            100
        )

        print(
            "Training done",
            duration
        )

        return {

            "status": "training_done",
            "result": result

        }

    except Exception as e:

        print(
            "Training error:",
            e
        )

        return {

            "status": "error",
            "message": str(e)

        }

    finally:

        gc.collect()