import socket


# =========================
# GET LOCAL IP
# =========================

def get_local_ip():

    try:

        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        # dummy connect
        s.connect(("8.8.8.8", 80))

        ip = s.getsockname()[0]

        s.close()

        return ip

    except Exception as e:

        print(
            "IP detection failed:",
            e
        )

        return "127.0.0.1"


# =========================
# NETWORK CONFIG
# =========================

LOCAL_IP = get_local_ip()

# MQTT selalu localhost
# karena broker jalan di mesin yang sama

MQTT_BROKER = "127.0.0.1"

# OTA harus pakai IP jaringan
# supaya ESP32 bisa akses

OTA_SERVER = LOCAL_IP

OTA_PORT = 8000


# =========================
# TASK CONFIG
# =========================

TASK_DISPATCH_INTERVAL = 1

RETRY_LIMIT = 3

TASK_TIMEOUT = 30

NODE_HEARTBEAT_TIMEOUT = 60


# =========================
# DEFAULT TASK
# =========================

DEFAULT_TASK = {

    "task": "random",

    "count": 10

}


# =========================
# DEBUG INFO
# =========================

print("================================")

print("Server Network IP :", LOCAL_IP)

print("MQTT Broker       :", MQTT_BROKER)

print("OTA Server        :", OTA_SERVER)

print("OTA Port          :", OTA_PORT)

print("================================")