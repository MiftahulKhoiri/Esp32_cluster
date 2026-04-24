"""
Modul coordinator untuk cluster Raspberry Pi.
Mengelola node, mendistribusikan tugas melalui MQTT,
memantau progres, dan menangani hasil.
Semua komentar dalam bahasa Indonesia.
"""

import json
import time
import uuid
import threading
import sys
import os
import signal

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
# KONFIGURASI PEMULIHAN MQTT
# =========================================================

mqtt_fail_count = 0          # Menghitung kegagalan koneksi MQTT berturut-turut
MAX_MQTT_FAIL = 5            # Batas maksimal kegagalan sebelum restart proses

reconnect_lock = threading.Lock()   # Lock untuk menghindari reconnect bersamaan

# =========================================================
# PENGAWAS LAYANAN (SERVICE WATCHDOG)
# =========================================================

last_loop_time = time.time()
WATCHDOG_TIMEOUT = 120       # Jika loop utama tidak update selama 120 detik, restart layanan

# =========================================================
# OUTPUT KONSOL SEDERHANA
# =========================================================

def print_event(message):
    """
    Mencetak pesan ke konsol.
    Digunakan untuk menampilkan kejadian penting secara real-time.
    """
    print(message)


last_progress = {}           # Menyimpan progres terakhir per node
PROGRESS_STEP = 10           # Progress hanya dicetak setiap kenaikan 10%


def print_progress(node, progress):
    """
    Mencetak progres task dari sebuah node jika kenaikannya >= PROGRESS_STEP.
    Menghindari spam di konsol.

    Parameter:
        node (str): ID node
        progress (int): Persentase progres (0-100)
    """
    last = last_progress.get(node)

    if last is None or progress >= last + PROGRESS_STEP:
        last_progress[node] = progress
        print(
            f"Progress {node}: {progress}%"
        )


# =========================================================
# STATUS
# =========================================================

state_lock = threading.Lock()   # Melindungi akses ke variabel status

ready_nodes = set()             # Himpunan node yang siap menerima task
node_list = []                  # Daftar node (diperbarui dari ready_nodes)
node_index = 0                  # Indeks untuk round‑robin pemilihan node

running_tasks = {}              # Task yang sedang berjalan: task_id -> info
completed_tasks = {}            # Task yang sudah selesai (tidak digunakan lebih lanjut di sini)

node_last_seen = {}             # Waktu terakhir node terlihat (heartbeat)

service_running = True          # Flag utama untuk menjaga loop tetap berjalan
shutdown_requested = False      # Menandakan proses shutdown telah diminta


# =========================================================
# DATABASE
# =========================================================

init_db()

print_event(
    "Database initialized"
)


# =========================================================
# MANAJEMEN NODE
# =========================================================

def update_node_list():
    """
    Memperbarui daftar node dari himpunan ready_nodes.
    Dipanggil setiap kali ready_nodes berubah.
    """
    global node_list

    with state_lock:
        node_list = list(
            ready_nodes
        )


def get_next_node():
    """
    Memilih node berikutnya secara round‑robin dari node_list.
    Mengembalikan None jika tidak ada node yang tersedia.
    """
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
# PEMERIKSAAN KESEHATAN NODE
# =========================================================

def check_node_health():
    """
    Mendeteksi node yang tidak mengirim heartbeat dalam
    NODE_HEARTBEAT_TIMEOUT detik, lalu menghapusnya dari ready_nodes.
    """
    now = time.time()
    dead_nodes = []

    with state_lock:
        for node, last_seen in list(
            node_last_seen.items()
        ):
            if now - last_seen > NODE_HEARTBEAT_TIMEOUT:
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
# PEMERIKSAAN TIMEOUT TASK
# =========================================================

def check_timeouts():
    """
    Memeriksa task yang sedang berjalan apakah melebihi TASK_TIMEOUT.
    Jika ya, status task diubah menjadi 'timeout'.
    """
    now = time.time()
    timed_out = []

    with state_lock:
        for task_id, info in list(
            running_tasks.items()
        ):
            start_time = info.get("start_time")
            if not start_time:
                continue
            if now - start_time > TASK_TIMEOUT:
                timed_out.append(task_id)

    for task_id in timed_out:
        print_event(
            f"Task timeout: {task_id}"
        )
        update_status(
            task_id,
            "timeout"
        )


# =========================================================
# SERVICE WATCHDOG
# =========================================================

def watchdog_monitor():
    """
    Thread yang memantau apakah loop utama masih berjalan.
    Jika last_loop_time tidak diperbarui selama WATCHDOG_TIMEOUT,
    layanan akan direstart menggunakan os.execv.
    """
    global last_loop_time

    while service_running:
        try:
            now = time.time()
            if now - last_loop_time > WATCHDOG_TIMEOUT:
                print_event(
                    "Watchdog timeout — restarting service"
                )
                time.sleep(2)
                os.execv(
                    sys.executable,
                    [sys.executable] + sys.argv
                )
            time.sleep(10)
        except Exception:
            logger.exception("Watchdog error")


# =========================================================
# PEMULIHAN KONEKSI MQTT
# =========================================================

def reconnect_mqtt():
    """
    Mencoba menyambungkan kembali ke broker MQTT setelah putus.
    Jika gagal hingga MAX_MQTT_FAIL kali, proses di-restart.
    Menggunakan lock untuk mencegah pemanggilan bersamaan.
    """
    global mqtt_fail_count

    if shutdown_requested:
        return

    with reconnect_lock:
        try:
            print_event("Reconnecting MQTT...")
            client.loop_stop()
            client.disconnect()
        except:
            pass

        while not shutdown_requested:
            try:
                client.connect(
                    MQTT_BROKER,
                    1883,
                    60
                )
                client.loop_start()
                mqtt_fail_count = 0
                print_event("MQTT reconnected")
                return
            except Exception:
                mqtt_fail_count += 1
                print_event(
                    f"MQTT reconnect failed: {mqtt_fail_count}"
                )
                if mqtt_fail_count >= MAX_MQTT_FAIL:
                    print_event(
                        "Too many MQTT failures — restarting process"
                    )
                    time.sleep(2)
                    os.execv(
                        sys.executable,
                        [sys.executable] + sys.argv
                    )
                time.sleep(5)


# =========================================================
# SHUTDOWN YANG TERKENDALI
# =========================================================

def shutdown_handler(signum, frame):
    """
    Menangani sinyal terminasi (SIGINT, SIGTERM) secara bersih:
    - Menghentikan loop utama.
    - Memutus koneksi MQTT.
    - Keluar dengan kode 0.
    """
    global service_running
    global shutdown_requested

    if shutdown_requested:
        return

    shutdown_requested = True
    print_event(
        f"Shutdown signal received: {signum}"
    )
    service_running = False

    try:
        client.loop_stop()
    except:
        pass

    try:
        client.disconnect()
    except:
        pass

    print_event("Shutdown complete")
    sys.exit(0)


# =========================================================
# REGISTRASI SINYAL SECARA AMAN
# =========================================================

try:
    if threading.current_thread() is threading.main_thread():
        signal.signal(
            signal.SIGINT,
            shutdown_handler
        )
        signal.signal(
            signal.SIGTERM,
            shutdown_handler
        )
except Exception:
    print_event(
        "Signal handler skipped"
    )


# =========================================================
# CALLBACK MQTT
# =========================================================

def on_connect(client, userdata, flags, rc):
    """
    Callback saat terhubung ke broker.
    Jika berhasil (rc=0), subscribe ke topik yang diperlukan.
    """
    if rc == 0:
        print_event("MQTT connected")
        client.subscribe("cluster/status/+")
        client.subscribe("cluster/task_status/+")
        client.subscribe("cluster/result/+")
        client.subscribe("cluster/progress/+")


def on_disconnect(client, userdata, rc):
    """
    Callback saat koneksi terputus. Memanggil prosedur reconnect.
    """
    print_event(
        f"MQTT disconnected: {rc}"
    )
    reconnect_mqtt()


def on_message(client, userdata, msg):
    """
    Callback saat pesan MQTT diterima.
    Menangani topik status node, progres, dan hasil task.
    """
    topic = msg.topic
    payload = json.loads(msg.payload)

    if topic.startswith("cluster/status"):
        # Update status node (ready/online/offline)
        node = payload.get("node")
        status = payload.get("status")

        with state_lock:
            node_last_seen[node] = time.time()

            if status in ["ready", "online"]:
                if node not in ready_nodes:
                    ready_nodes.add(node)
                    print_event(f"Node ready: {node}")
            elif status == "offline":
                if node in ready_nodes:
                    ready_nodes.discard(node)
                    print_event(f"Node offline: {node}")

        update_node_list()

    elif topic.startswith("cluster/progress"):
        # Terima laporan progres dari node
        node = payload.get("node")
        progress = payload.get("progress", 0)
        print_progress(node, progress)
        update_progress(node, payload)

    elif topic.startswith("cluster/result"):
        # Hasil akhir task diterima
        result = payload.get("result")
        filename = result.get("filename")
        handle_result(
            payload.get("node"),
            filename,
            result.get("data")
        )
        print_event(f"Result stored: {filename}")


# =========================================================
# SETUP KLIEN MQTT
# =========================================================

client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.connect(
    MQTT_BROKER,
    1883,
    60
)
client.loop_start()


# =========================================================
# TUGAS AWAL
# =========================================================

def add_task(task):
    """
    Menambahkan task baru ke database dengan ID unik.
    Mencetak event saat task ditambahkan.
    """
    task_id = str(uuid.uuid4())
    task["task_id"] = task_id
    insert_task(task)
    print_event(f"Task added: {task_id}")


# Tambahkan task default saat koordinator dimulai
add_task(
    DEFAULT_TASK.copy()
)


# =========================================================
# LOOP UTAMA KOORDINATOR
# =========================================================

def coordinator_loop():
    """
    Loop utama koordinator.
    Secara berkala memeriksa kesehatan node dan timeout task.
    """
    global last_loop_time

    print_event("Coordinator started")

    while service_running:
        try:
            last_loop_time = time.time()
            check_node_health()
            check_timeouts()
            time.sleep(TASK_DISPATCH_INTERVAL)
        except Exception:
            logger.exception("Coordinator error")
            time.sleep(2)


# =========================================================
# MULAI THREAD
# =========================================================

# Thread pengawas untuk mendeteksi hang
watchdog_thread = threading.Thread(
    target=watchdog_monitor,
    daemon=True
)
watchdog_thread.start()

# Thread utama koordinator
coordinator_thread = threading.Thread(
    target=coordinator_loop,
    daemon=True
)
coordinator_thread.start()