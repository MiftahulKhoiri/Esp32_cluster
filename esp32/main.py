# Import library MQTT client untuk MicroPython (umqtt.simple)
from umqtt.simple import MQTTClient
import ujson           # Library JSON untuk MicroPython
import time            # Modul waktu
import machine         # Akses hardware (reset, penyebab reboot)
import gc              # Garbage collector
import socket          # Untuk resolusi DNS

import config          # File konfigurasi lokal

# Ambil konstanta dari file config
from config import (
    MQTT_BROKER,
    NODE_ID,
    HEARTBEAT_INTERVAL
)

# Fungsi untuk menjalankan tugas yang diterima dari cluster
from worker import run_task
# Fungsi untuk mengirim status sistem (RAM, uptime, dll.)
from system_monitor import send_system_status

# Modul koneksi WiFi
from connectionwifi import (
    connect_wifi,
    ensure_connection
)

# Modul pembaruan OTA (Over-The-Air)
import ota

# Coba impor modul LED; jika tidak ada, set flag LED_AVAILABLE = False
try:
    import led
    LED_AVAILABLE = True
except Exception:
    LED_AVAILABLE = False


# -------------------- Variabel Global --------------------
client = None
last_heartbeat = 0
last_gc = 0
GC_INTERVAL = config.GC_INTERVAL
mqtt_fail_count = 0


# =========================
# SAFE PUBLISH
# =========================

def safe_publish(topic, payload):
    global client

    try:
        client.publish(topic, payload)
    except Exception as e:
        print("Publish failed:", e)
        raise


# =========================
# DNS RESOLVE SERVER
# =========================

def resolve_server():
    for _ in range(config.DNS_RESOLVE_RETRY):
        try:
            addr = socket.getaddrinfo(
                config.MQTT_BROKER,
                config.MQTT_PORT
            )[0][-1][0]
            print("Resolved server:", addr)
            return addr
        except Exception as e:
            print("DNS resolve failed:", e)
            if config.SERVER_FALLBACK_IP:
                print("Using fallback IP")
                return config.SERVER_FALLBACK_IP
            time.sleep(config.DNS_RESOLVE_DELAY)

    raise RuntimeError("Server resolve failed")


# =========================
# SAFE RESULT SEND
# =========================

def send_result(result):
    try:
        topic = "cluster/result/" + NODE_ID
        payload = ujson.dumps({
            "node": NODE_ID,
            "result": result
        })

        if len(payload) > config.MQTT_MAX_PAYLOAD:
            print("Result too large")
            payload = ujson.dumps({
                "node": NODE_ID,
                "result": {
                    "status": "error",
                    "message": "result too large"
                }
            })

        safe_publish(topic, payload)

    except Exception as e:
        print("Send result error:", e)


# =========================
# TASK STATUS
# =========================

def send_task_status(task_id, status):
    try:
        payload = ujson.dumps({
            "node": NODE_ID,
            "task_id": task_id,
            "status": status,
            "timestamp": time.ticks_ms()
        })
        topic = "cluster/task_status/" + NODE_ID
        safe_publish(topic, payload)
    except Exception as e:
        print("Task status error:", e)


# =========================
# READY STATE
# =========================

def set_ready_state():
    try:
        payload = ujson.dumps({
            "node": NODE_ID,
            "status": "ready"
        })
        safe_publish("cluster/status/" + NODE_ID, payload)

        if LED_AVAILABLE:
            led.set_state(led.STATE_READY)

        print("Node READY")
    except Exception as e:
        print("Ready error:", e)


# =========================
# OTA UPDATE
# =========================

def handle_ota_command():
    print("OTA command received")
    if LED_AVAILABLE:
        led.set_state(led.STATE_OTA)
    ota.perform_update()


# =========================
# MESSAGE CALLBACK
# =========================

def on_message(topic, msg):
    try:
        topic = topic.decode()

        if topic == "cluster/ota/update":
            handle_ota_command()
            return

        if topic == "cluster/task/" + NODE_ID:
            print("Task received")
            data = ujson.loads(msg)
            task_id = data.get("task_id", "unknown")

            send_task_status(task_id, "received")

            if LED_AVAILABLE:
                led.set_state(led.STATE_RUNNING)

            send_task_status(task_id, "running")

            try:
                result = run_task(data)
            except Exception as e:
                print("Task crash:", e)
                result = {
                    "status": "error",
                    "message": str(e)
                }

            send_result(result)

            final_status = result.get("status", "done")
            send_task_status(task_id, final_status)

            set_ready_state()

    except Exception as e:
        print("Task error:", e)
        send_task_status("unknown", "error")


# =========================
# REGISTER NODE
# =========================

def register_node():
    payload = ujson.dumps({
        "node": NODE_ID,
        "status": "online"
    })
    safe_publish("cluster/register", payload)


# =========================
# PERIODIC GC
# =========================

def periodic_gc():
    global last_gc

    now = time.ticks_ms()

    if time.ticks_diff(now, last_gc) < GC_INTERVAL * 1000:
        return

    last_gc = now

    try:
        before = gc.mem_free()
        gc.collect()
        after = gc.mem_free()
        print("GC:", before, "->", after)
    except Exception as e:
        print("GC error:", e)


# =========================
# MQTT CONNECT
# =========================

def connect_mqtt():
    global client
    global mqtt_fail_count

    while True:
        try:
            print("Connecting MQTT...")
            server_ip = resolve_server()

            if client:
                try:
                    client.disconnect()
                except Exception:
                    pass
                client = None

            gc.collect()

            client = MQTTClient(
                client_id=NODE_ID,
                server=server_ip,
                port=config.MQTT_PORT,
                keepalive=config.MQTT_KEEPALIVE
            )

            client.set_last_will(
                "cluster/status/" + NODE_ID,
                ujson.dumps({
                    "node": NODE_ID,
                    "status": "offline"
                }),
                retain=False,
                qos=0
            )

            client.set_callback(on_message)
            client.connect()

            client.subscribe("cluster/task/" + NODE_ID)
            client.subscribe("cluster/ota/update")

            print("MQTT connected:", server_ip)
            mqtt_fail_count = 0

            register_node()
            set_ready_state()
            return

        except Exception as e:
            mqtt_fail_count += 1
            print("MQTT failed:", e)
            print("MQTT failure count:", mqtt_fail_count)

            if mqtt_fail_count >= config.MQTT_MAX_FAILURE:
                print("Too many MQTT failures — rebooting")
                time.sleep(config.REBOOT_DELAY)
                machine.reset()

            time.sleep(config.MQTT_RECONNECT_DELAY)


# =========================
# HEARTBEAT
# =========================

def send_heartbeat():
    global last_heartbeat

    now = time.ticks_ms()

    if time.ticks_diff(now, last_heartbeat) < HEARTBEAT_INTERVAL * 1000:
        return

    last_heartbeat = now

    try:
        payload = ujson.dumps({
            "node": NODE_ID,
            "status": "online"
        })
        safe_publish("cluster/status/" + NODE_ID, payload)
    except Exception as e:
        print("Heartbeat error:", e)
        raise


# =========================
# MAIN LOOP
# =========================

def main():
    print("Booting node:", NODE_ID)

    try:
        cause = machine.reset_cause()
        print("Reset cause:", cause)
    except Exception:
        pass

    if LED_AVAILABLE:
        led.set_state(led.STATE_WIFI)

    connect_wifi()
    time.sleep(2)

    try:
        ota.perform_update()
    except Exception as e:
        print("OTA error:", e)

    connect_mqtt()

    while True:
        try:
            ensure_connection()
            client.ping()
            client.check_msg()

            send_heartbeat()
            send_system_status(client)
            periodic_gc()

        except Exception as e:
            print("MQTT error:", e)
            time.sleep(2)
            connect_mqtt()

        time.sleep(0.1)


main()