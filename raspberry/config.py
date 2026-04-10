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

        # connect ke internet dummy
        s.connect(("8.8.8.8", 80))

        ip = s.getsockname()[0]

        s.close()

        return ip

    except Exception as e:

        print("IP detection failed:", e)

        return "127.0.0.1"


# =========================
# NETWORK CONFIG
# =========================

LOCAL_IP = get_local_ip()

MQTT_BROKER = LOCAL_IP

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

print("Server IP:", LOCAL_IP)