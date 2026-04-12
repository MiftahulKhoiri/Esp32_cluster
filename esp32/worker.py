import time
import os
import base64
import sys
import ujson
import machine

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

TRAINING_TIMEOUT = 300   # seconds watchdog


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


# =========================
# RESUME META
# =========================

def get_meta_path(filename):

    return DATA_DIR + "/" + filename + ".meta"


def load_last_chunk(filename):

    path = get_meta_path(filename)

    if path not in os.listdir(DATA_DIR):

        return 0

    try:

        with open(path, "r") as f:

            meta = ujson.loads(f.read())

            return meta.get("last_chunk", 0)

    except:

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

    path = get_meta_path(filename)

    try:

        if filename + ".meta" in os.listdir(DATA_DIR):

            os.remove(path)

    except:

        pass


# =========================
# WATCHDOG
# =========================

def start_watchdog():

    wdt = machine.WDT(timeout=TRAINING_TIMEOUT * 1000)

    return wdt


# =========================
# MAIN TASK
# =========================

def run_task(data):

    init_directories()

    try:

        if LED_AVAILABLE:
            led.set_state(led.STATE_RUNNING)

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
            led.set_state(led.STATE_READY)


# =========================
# UPLOAD PROGRAM
# =========================

def handle_upload_program(task):

    filename = task.get("filename")

    data_base64 = task.get("data")

    send_progress("upload_program", 0)

    path = PROGRAM_DIR + "/" + filename

    data = base64.b64decode(data_base64)

    with open(path, "wb") as f:

        f.write(data)

    module_name = filename.replace(".py", "")

    reload_module(module_name)

    send_progress("upload_program", 100)

    print("Program saved:", filename)

    return {

        "status": "program_updated"

    }


# =========================
# UPLOAD CHUNK (RESUME)
# =========================

def handle_upload_chunk(task):

    filename = task.get("filename")

    chunk_index = task.get("chunk_index")

    total_chunks = task.get("total_chunks")

    auto_train = task.get("auto_train", False)

    last_chunk = load_last_chunk(filename)

    if chunk_index <= last_chunk:

        print(

            "Skip chunk",
            chunk_index

        )

        return {

            "status": "skip"

        }

    data = base64.b64decode(

        task.get("data")

    )

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

    # FILE COMPLETE

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
# TRAINING + WATCHDOG
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

    reload_module(module_name)

    wdt = start_watchdog()

    send_progress("training", 10)

    module = __import__(module_name)

    send_progress("training", 40)

    start_time = time.time()

    result = None

    while True:

        wdt.feed()

        result = module.run()

        break

    duration = time.time() - start_time

    send_progress("training", 100)

    print(

        "Training done",
        duration

    )

    return {

        "status": "training_done",
        "result": result

    }