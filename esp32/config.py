# =========================
# WIFI CONFIG
# =========================

WIFI_SSID = "NamaWiFi"
WIFI_PASSWORD = "PasswordWiFi"


# =========================
# SERVER CONFIG
# =========================
# Gunakan hostname, bukan IP
# Server harus menjalankan mDNS

SERVER_HOSTNAME = "cluster-server.local"

# Fallback jika mDNS gagal
SERVER_FALLBACK_IP = None
# contoh:
# SERVER_FALLBACK_IP = "192.168.1.10"


# =========================
# MQTT CONFIG
# =========================

MQTT_BROKER = SERVER_HOSTNAME
MQTT_PORT = 1883

MQTT_KEEPALIVE = 60
MQTT_RECONNECT_DELAY = 5


# =========================
# NODE CONFIG
# =========================

NODE_ID = "node1"

NODE_ROLE = "worker"

AUTO_RECONNECT = True


# =========================
# OTA CONFIG
# =========================

OTA_SERVER = SERVER_HOSTNAME
OTA_PORT = 8000

VERSION = "1.0"

OTA_TIMEOUT = 30


# =========================
# NETWORK
# =========================

REQUEST_TIMEOUT = 10

HEARTBEAT_INTERVAL = 30

DNS_RESOLVE_RETRY = 3
DNS_RESOLVE_DELAY = 2


# =========================
# DEBUG
# =========================

DEBUG = True
LOG_NETWORK = True