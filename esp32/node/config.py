# =========================
# WIFI CONFIG
# =========================

WIFI_SSID = "CLUSTER-NODE"
WIFI_PASSWORD = "root123"

# Timeout koneksi WiFi (detik)
WIFI_CONNECT_TIMEOUT = 20

# Delay retry WiFi
WIFI_RETRY_DELAY = 5

# Maks retry sebelum reboot
WIFI_MAX_RETRIES = 5


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

# Keepalive MQTT
MQTT_KEEPALIVE = 60

# Delay reconnect MQTT
MQTT_RECONNECT_DELAY = 5

# Maks retry MQTT sebelum reboot
MQTT_MAX_FAILURE = 5

# Ping interval MQTT (health check)
MQTT_PING_INTERVAL = 20

# Maks payload safety
MQTT_MAX_PAYLOAD = 50000


# =========================
# NODE CONFIG
# =========================

NODE_ID = "node1"
# sesuaikan dengan jumlah node yang ad

NODE_ROLE = "worker"

AUTO_RECONNECT = True

# Interval status node
NODE_STATUS_INTERVAL = 30


# =========================
# OTA CONFIG
# =========================

OTA_SERVER = SERVER_HOSTNAME

OTA_PORT = 8000

VERSION = "1.0"

# Timeout request OTA
OTA_TIMEOUT = 30

# Retry OTA
OTA_MAX_RETRIES = 3

# Delay retry OTA
OTA_RETRY_DELAY = 2

# Chunk size download
OTA_CHUNK_SIZE = 512


# =========================
# NETWORK
# =========================

# Timeout HTTP / socket
REQUEST_TIMEOUT = 10

# Interval heartbeat MQTT
HEARTBEAT_INTERVAL = 30

# DNS retry
DNS_RESOLVE_RETRY = 3

# Delay DNS retry
DNS_RESOLVE_DELAY = 2

# Network watchdog
NETWORK_WATCHDOG_INTERVAL = 60


# =========================
# MEMORY
# =========================

# Interval garbage collector
GC_INTERVAL = 60

# Memory warning threshold (KB)
MEMORY_WARNING_KB = 40

# Memory critical threshold (KB)
MEMORY_CRITICAL_KB = 20


# =========================
# SYSTEM
# =========================

# Delay reboot
REBOOT_DELAY = 2

# Maks failure global sebelum reboot
MAX_FAILURE_BEFORE_RESET = 3


# =========================
# DEBUG
# =========================

DEBUG = True

LOG_NETWORK = True

LOG_MQTT = True

LOG_OTA = True