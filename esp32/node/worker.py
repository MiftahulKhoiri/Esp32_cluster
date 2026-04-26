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
        """Decode string Base64 menjadi bytes menggunakan ubinascii (MicroPython)."""
        return _b64.a2b_base64(data)
except ImportError:
    import base64 as _b64
    def b64decode(data):
        """Decode string Base64 menjadi bytes menggunakan modul base64 standar."""
        return _b64.b64decode(data)


# Coba impor modul LED, jika gagal set LED_AVAILABLE = False
try:
    import led
    LED_AVAILABLE = True
except Exception:
    LED_AVAILABLE = False


# =========================
# CONFIG
# =========================

PROGRAM_DIR = "programs"
DATA_DIR = "data"

DEFAULT_TIMEOUT = 10
TRAINING_TIMEOUT = 300

MIN_FREE_SPACE_KB = 100


# =========================
# DISK SPACE CHECK
# =========================

def get_free_space_kb():
    """
    Mengecek ruang kosong pada filesystem root ('/') dalam satuan KB.
    Mengembalikan jumlah KB bebas, atau 0 jika gagal.
    """
    try:
        stat = os.statvfs("/")
        block_size = stat[0]
        free_blocks = stat[3]
        free_bytes = block_size * free_blocks
        return free_bytes // 1024
    except Exception as e:
        print("Disk check error:", e)
        return 0


# =========================
# ATOMIC WRITE
# =========================

def atomic_write(path, data, mode="wb"):
    """
    Menulis data ke file secara atomik menggunakan file temporer.
    """
    temp_path = path + ".tmp"

    try:
        with open(temp_path, mode) as f:
            f.write(data)
            try:
                f.flush()
            except Exception:
                pass

        if path in os.listdir():
            os.remove(path)

        os.rename(temp_path, path)
        return True

    except Exception as e:
        print("Atomic write error:", e)
        try:
            if temp_path in os.listdir():
                os.remove(temp_path)
        except Exception:
            pass
        return False


# =========================
# INIT DIRECTORIES
# =========================

def init_directories():
    """
    Memastikan direktori PROGRAM_DIR dan DATA_DIR sudah ada.
    """
    if PROGRAM_DIR not in os.listdir():
        os.mkdir(PROGRAM_DIR)
    if DATA_DIR not in os.listdir():
        os.mkdir(DATA_DIR)


# =========================
# PROGRESS
# =========================

def send_progress(stage, percent):
    """
    Mengirim laporan progres task ke broker MQTT.
    """
    try:
        from config import NODE_ID
        from main import client

        if client is None:
            return

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
    """
    Memuat ulang modul Python dengan menghapusnya dari sys.modules.
    """
    if module_name in sys.modules:
        print("Reloading:", module_name)
        del sys.modules[module_name]
        gc.collect()


# =========================
# WATCHDOG
# =========================

def start_watchdog():
    """
    Menginisialisasi hardware watchdog timer (WDT).
    """
    try:
        timeout_ms = TRAINING_TIMEOUT * 1000
        return machine.WDT(timeout=timeout_ms)
    except Exception:
        print("WDT fallback to 120s")
        return machine.WDT(timeout=120000)


# =========================
# MAIN TASK
# =========================

def run_task(data):
    """
    Fungsi utama yang dipanggil saat node menerima tugas dari cluster.
    """
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
# TRAINING
# =========================

def handle_training(task):
    """
    Menjalankan program training yang ada di PROGRAM_DIR.
    """
    program = task.get("program", "train_model.py")
    module_name = program.replace(".py", "")

    if PROGRAM_DIR not in sys.path:
        sys.path.append(PROGRAM_DIR)

    reload_module(module_name)

    wdt = start_watchdog()

    send_progress("training", 10)

    try:
        module = __import__(module_name)

        send_progress("training", 40)

        start_time = time.ticks_ms()

        wdt.feed()

        result = module.run()

        wdt.feed()

        duration = time.ticks_diff(
            time.ticks_ms(),
            start_time
        ) / 1000

        send_progress("training", 100)

        print("Training done", duration)

        return {
            "status": "training_done",
            "result": result
        }

    except Exception as e:
        print("Training error:", e)
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        gc.collect()