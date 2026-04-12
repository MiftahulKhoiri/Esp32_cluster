import time
import os
import base64
import sys

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


# =========================
# INIT DIRECTORIES
# =========================

def init_directories():

    try:

        if PROGRAM_DIR not in os.listdir():
            os.mkdir(PROGRAM_DIR)

        if DATA_DIR not in os.listdir():
            os.mkdir(DATA_DIR)

    except Exception as e:

        print("Directory init error:", e)


# =========================
# PROGRESS SENDER
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

        import ujson

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

    try:

        if module_name in sys.modules:

            print(
                "Reloading module:",
                module_name
            )

            del sys.modules[module_name]

        return True

    except Exception as e:

        print(
            "Reload module error:",
            e
        )

        return False


# =========================
# MAIN ENTRY
# =========================

def run_task(data):

    start_time = time.time()

    try:

        init_directories()

        if LED_AVAILABLE:
            led.set_state(led.STATE_RUNNING)

        if not isinstance(data, dict):

            return error_result(
                "unknown",
                "Invalid task format"
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

        task_type = data.get("type")

        if not task_type:

            return error_result(
                task_id,
                "Missing type field"
            )

        # =====================
        # DISPATCH
        # =====================

        if task_type == "upload_program":

            result = handle_upload_program(data)

        elif task_type == "upload_chunk":

            result = handle_upload_chunk(data)

        elif task_type == "train":

            result = handle_training(data)

        elif task_type == "status":

            result = task_status()

        else:

            return error_result(
                task_id,
                "Unknown task: {}".format(task_type)
            )

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
# HANDLE UPLOAD PROGRAM
# =========================

def handle_upload_program(task):

    try:

        filename = task.get("filename")

        data_base64 = task.get("data")

        if not filename:

            raise ValueError(
                "filename missing"
            )

        send_progress(
            "upload_program",
            0
        )

        file_path = PROGRAM_DIR + "/" + filename

        data = base64.b64decode(
            data_base64
        )

        with open(
            file_path,
            "wb"
        ) as f:

            f.write(data)

        module_name = filename.replace(
            ".py",
            ""
        )

        reload_module(
            module_name
        )

        send_progress(
            "upload_program",
            100
        )

        print(
            "Program updated:",
            file_path
        )

        return {

            "status": "program_updated",
            "filename": filename

        }

    except Exception as e:

        print(
            "Upload program error:",
            e
        )

        raise


# =========================
# HANDLE FILE CHUNK
# =========================

def handle_upload_chunk(task):

    try:

        filename = task.get("filename")

        chunk_index = task.get(
            "chunk_index"
        )

        total_chunks = task.get(
            "total_chunks"
        )

        data_base64 = task.get("data")

        auto_train = task.get(
            "auto_train",
            False
        )

        if not filename:

            raise ValueError(
                "filename missing"
            )

        file_path = DATA_DIR + "/" + filename

        data = base64.b64decode(
            data_base64
        )

        mode = "ab"

        if chunk_index == 1:
            mode = "wb"

        with open(
            file_path,
            mode
        ) as f:

            f.write(data)

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

        # =====================
        # FILE COMPLETE
        # =====================

        if chunk_index == total_chunks:

            print(
                "File completed:",
                filename
            )

            if auto_train:

                return handle_training({

                    "program": "train_model.py"

                })

        return {

            "status": "chunk_received"

        }

    except Exception as e:

        print(
            "Upload chunk error:",
            e
        )

        raise


# =========================
# HANDLE TRAINING
# =========================

def handle_training(task):

    try:

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

        send_progress(
            "training",
            10
        )

        module = __import__(
            module_name
        )

        send_progress(
            "training",
            40
        )

        result = module.run()

        send_progress(
            "training",
            100
        )

        print(
            "Training completed"
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

        raise


# =========================
# TASK STATUS
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
# TASK ID
# =========================

def generate_task_id():

    return "local_" + str(
        time.ticks_ms()
    )