# =========================================================
# IMPORTS
# =========================================================

import network
import time
import machine
import gc
import os
import sys
import socket

import ujson
import urequests
from umqtt.simple import MQTTClient

from machine import Pin, Timer

from config import (
    WIFI_SSID,
    WIFI_PASSWORD,
    MQTT_BROKER,
    NODE_ID,
    HEARTBEAT_INTERVAL,
    OTA_SERVER,
    OTA_PORT,
    VERSION,
    REQUEST_TIMEOUT
)

# =========================================================
# GLOBAL STATE
# =========================================================

client = None

last_heartbeat = 0
last_report = 0

# =========================================================
# LED MODULE
# =========================================================

LED_PIN = 2

STATE_IDLE = "idle"
STATE_WIFI = "wifi_connecting"
STATE_WIFI_CONNECTED = "wifi_connected"
STATE_OTA = "ota_updating"
STATE_MQTT = "mqtt_connected"
STATE_RUNNING = "running"
STATE_ERROR = "error"
STATE_READY = "ready"

PERIOD_WIFI = 500
PERIOD_OTA = 100
PERIOD_RUNNING = 1000
PERIOD_ERROR = 2000

_led = None
_timer = Timer(1)
_state = STATE_IDLE


def led_init(pin=LED_PIN):
    global _led
    if _led is None:
        _led = Pin(pin, Pin.OUT)
        _led.value(0)


def _toggle(timer):
    try:
        if _led:
            _led.value(not _led.value())
    except Exception:
        pass


def led_stop():
    try:
        _timer.deinit()
    except:
        pass

    if _led:
        _led.value(0)


def set_led_state(new_state):
    global _state

    if _led is None:
        led_init()

    if new_state == _state:
        return

    _state = new_state

    try:
        _timer.deinit()
    except:
        pass

    if new_state == STATE_IDLE:
        _led.value(0)

    elif new_state == STATE_WIFI:
        _timer.init(
            period=PERIOD_WIFI,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == STATE_WIFI_CONNECTED:
        _led.value(1)

    elif new_state == STATE_MQTT:
        _led.value(1)

    elif new_state == STATE_OTA:
        _timer.init(
            period=PERIOD_OTA,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == STATE_RUNNING:
        _timer.init(
            period=PERIOD_RUNNING,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == STATE_ERROR:
        _timer.init(
            period=PERIOD_ERROR,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == STATE_READY:
        _led.value(1)


# =========================================================
# WIFI MODULE
# =========================================================

MAX_RETRIES = 5
RETRY_DELAY = 5


def reset_wifi():

    wlan = network.WLAN(network.STA_IF)

    try:
        wlan.disconnect()
    except:
        pass

    wlan.active(False)
    time.sleep(1)

    wlan.active(True)
    time.sleep(1)

    gc.collect()

    return wlan


def connect_wifi(timeout=20, retry=True):

    retries = 0

    while True:

        wlan = reset_wifi()

        print("Connecting WiFi...")

        set_led_state(STATE_WIFI)

        try:
            wlan.connect(
                WIFI_SSID,
                WIFI_PASSWORD
            )

        except OSError as e:

            print("Connect error:", e)

            retries += 1

            if retries >= MAX_RETRIES:
                return False

            time.sleep(RETRY_DELAY)
            continue

        start = time.time()

        while True:

            if wlan.isconnected():

                print("WiFi connected")

                print("IP:", wlan.ifconfig()[0])

                set_led_state(STATE_WIFI_CONNECTED)

                return True

            if time.time() - start > timeout:

                print("WiFi timeout")

                break

            time.sleep(1)

        retries += 1

        if not retry or retries >= MAX_RETRIES:

            print("WiFi failed")

            set_led_state(STATE_ERROR)

            return False

        print("Retrying WiFi")

        time.sleep(RETRY_DELAY)


def ensure_connection():

    wlan = network.WLAN(network.STA_IF)

    if not wlan.isconnected():

        print("WiFi lost")

        connect_wifi()


# =========================================================
# OTA MODULE
# =========================================================

TEMP_FILE = "main_new.py"
TARGET_FILE = "main.py"


def get_url(path):

    return "http://{}:{}/{}".format(
        OTA_SERVER,
        OTA_PORT,
        path
    )


def check_update():

    for attempt in range(3):

        try:

            print("Checking update")

            socket.setdefaulttimeout(
                REQUEST_TIMEOUT
            )

            url = get_url("version")

            response = urequests.get(url)

            data = response.json()

            response.close()

            server_version = data["version"]

            print("Current:", VERSION)
            print("Server :", server_version)

            if server_version != VERSION:

                print("Update available")

                return True

            return False

        except Exception as e:

            print("Update check failed:", e)

            time.sleep(2)

    return False


def download_firmware():

    for attempt in range(3):

        try:

            socket.setdefaulttimeout(
                REQUEST_TIMEOUT
            )

            set_led_state(STATE_OTA)

            print("Downloading firmware")

            url = get_url("firmware")

            response = urequests.get(url)

            size = 0

            with open(
                TEMP_FILE,
                "wb"
            ) as f:

                while True:

                    chunk = response.raw.read(
                        512
                    )

                    if not chunk:
                        break

                    f.write(chunk)

                    size += len(chunk)

            response.close()

            if size == 0:
                return False

            print("Downloaded:", size)

            return True

        except Exception as e:

            print("Download failed:", e)

            time.sleep(2)

    return False


def apply_update():

    try:

        if TARGET_FILE in os.listdir():

            os.remove(
                TARGET_FILE
            )

        os.rename(
            TEMP_FILE,
            TARGET_FILE
        )

        print("Firmware replaced")

        return True

    except Exception as e:

        print("Apply update failed:", e)

        return False


def perform_update():

    try:

        if not check_update():
            return False

        if not download_firmware():
            return False

        if not apply_update():
            return False

        print("Restarting device")

        time.sleep(2)

        machine.reset()

    except Exception as e:

        print("OTA error:", e)

        return False


# =========================================================
# SYSTEM MONITOR
# =========================================================

MONITOR_INTERVAL = 15
MEMORY_WARNING_KB = 40
MEMORY_CRITICAL_KB = 20


def get_memory_info():

    gc.collect()

    free = gc.mem_free()
    alloc = gc.mem_alloc()

    total = free + alloc

    return {

        "free_kb": free // 1024,
        "used_kb": alloc // 1024,
        "percent": int(
            (alloc / total) * 100
        )
    }


def get_flash_usage():

    try:

        stat = os.statvfs("/")

        block_size = stat[0]

        total_blocks = stat[2]
        free_blocks = stat[3]

        total = block_size * total_blocks
        free = block_size * free_blocks

        used = total - free

        return {

            "total_kb": total // 1024,
            "free_kb": free // 1024,
            "percent": int(
                (used / total) * 100
            )
        }

    except Exception:

        return {

            "total_kb": 0,
            "free_kb": 0,
            "percent": 0
        }


def get_temperature():

    try:
        return int(machine.temperature())
    except:
        return -1


def send_system_status():

    global last_report

    now = time.time()

    if now - last_report < MONITOR_INTERVAL:
        return

    last_report = now

    try:

        mem = get_memory_info()

        flash = get_flash_usage()

        payload = {

            "node": NODE_ID,
            "stage": "system",

            "memory_free_kb": mem["free_kb"],
            "memory_used_kb": mem["used_kb"],

            "flash_free_kb": flash["free_kb"],
            "flash_percent": flash["percent"],

            "temperature": get_temperature()

        }

        if client:

            client.publish(

                "cluster/progress/" + NODE_ID,

                ujson.dumps(payload)

            )

        if mem["free_kb"] < MEMORY_CRITICAL_KB:

            print("CRITICAL memory")

            machine.reset()

    except Exception as e:

        print("System monitor error:", e)


# =========================================================
# WORKER MODULE
# =========================================================

PROGRAM_DIR = "programs"
DATA_DIR = "data"

DEFAULT_TIMEOUT = 10
TRAINING_TIMEOUT = 300


def init_directories():

    if PROGRAM_DIR not in os.listdir():

        os.mkdir(PROGRAM_DIR)

    if DATA_DIR not in os.listdir():

        os.mkdir(DATA_DIR)


def send_progress(stage, percent):

    try:

        payload = {

            "node": NODE_ID,
            "stage": stage,
            "progress": percent

        }

        if client:

            client.publish(

                "cluster/progress/" + NODE_ID,

                ujson.dumps(payload)

            )

    except Exception as e:

        print("Progress error:", e)


def run_task(data):

    init_directories()

    try:

        set_led_state(STATE_RUNNING)

        task_type = data.get("type")

        if task_type == "train":

            send_progress(
                "training",
                100
            )

            return {

                "status": "training_done"

            }

        return {

            "status": "done"

        }

    except Exception as e:

        return {

            "status": "error",
            "message": str(e)

        }

    finally:

        set_led_state(STATE_READY)


# =========================================================
# MQTT MODULE
# =========================================================

def send_result(result):

    try:

        topic = "cluster/result/" + NODE_ID

        payload = ujson.dumps({

            "node": NODE_ID,
            "result": result

        })

        client.publish(
            topic,
            payload
        )

    except Exception as e:

        print("Send result error:", e)


def send_task_status(task_id, status):

    try:

        payload = ujson.dumps({

            "node": NODE_ID,
            "task_id": task_id,
            "status": status,

            "timestamp": time.time()

        })

        topic = "cluster/task_status/" + NODE_ID

        client.publish(
            topic,
            payload
        )

    except Exception as e:

        print("Task status error:", e)


def set_ready_state():

    try:

        payload = ujson.dumps({

            "node": NODE_ID,
            "status": "ready"

        })

        client.publish(

            "cluster/status/" + NODE_ID,

            payload

        )

        set_led_state(STATE_READY)

        print("Node READY")

    except Exception as e:

        print("Ready error:", e)


def handle_ota_command():

    print("OTA command received")

    set_led_state(STATE_OTA)

    perform_update()


def on_message(topic, msg):

    try:

        topic = topic.decode()

        if topic == "cluster/ota/update":

            handle_ota_command()

            return

        if topic == "cluster/task/" + NODE_ID:

            print("Task received")

            data = ujson.loads(msg)

            task_id = data.get(
                "task_id",
                "unknown"
            )

            send_task_status(
                task_id,
                "received"
            )

            send_task_status(
                task_id,
                "running"
            )

            try:

                result = run_task(data)

            except Exception as e:

                result = {

                    "status": "error",
                    "message": str(e)

                }

            send_result(result)

            final_status = result.get(
                "status",
                "done"
            )

            send_task_status(
                task_id,
                final_status
            )

            set_ready_state()

    except Exception as e:

        print("Task error:", e)


def register_node():

    payload = ujson.dumps({

        "node": NODE_ID,
        "status": "online"

    })

    client.publish(
        "cluster/register",
        payload
    )


def connect_mqtt():

    global client

    while True:

        try:

            print("Connecting MQTT")

            if client:

                try:
                    client.disconnect()
                except:
                    pass

            client = MQTTClient(

                client_id=NODE_ID,

                server=MQTT_BROKER,

                keepalive=60

            )

            client.set_callback(
                on_message
            )

            client.connect()

            client.subscribe(
                "cluster/task/" + NODE_ID
            )

            client.subscribe(
                "cluster/ota/update"
            )

            print("MQTT connected")

            register_node()

            set_ready_state()

            return

        except Exception as e:

            print("MQTT failed:", e)

            time.sleep(5)


def send_heartbeat():

    global last_heartbeat

    now = time.time()

    if now - last_heartbeat < HEARTBEAT_INTERVAL:

        return

    last_heartbeat = now

    try:

        payload = ujson.dumps({

            "node": NODE_ID,

            "status": "online"

        })

        client.publish(

            "cluster/status/" + NODE_ID,

            payload

        )

    except Exception as e:

        print("Heartbeat error:", e)


# =========================================================
# MAIN LOOP
# =========================================================

def main():

    print("Booting node:", NODE_ID)

    set_led_state(STATE_WIFI)

    connect_wifi()

    time.sleep(2)

    try:

        perform_update()

    except Exception as e:

        print("OTA error:", e)

    connect_mqtt()

    while True:

        try:

            ensure_connection()

            client.check_msg()

            send_heartbeat()

            send_system_status()

        except Exception as e:

            print("MQTT error:", e)

            time.sleep(2)

            connect_mqtt()

        time.sleep(0.1)