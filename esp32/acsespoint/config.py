# =========================
# WIFI ACCESS POINT CONFIG
# =========================

# Nama WiFi Access Point
SSID = "CLUSTER-NODE"

# Password WiFi (minimal 8 karakter)
PASSWORD = "cluster123"

# Channel WiFi (1 - 13)
CHANNEL = 6

# Maksimal jumlah client
MAX_CLIENTS = 10

# IP Access Point
AP_IP = "192.168.4.1"

# Subnet
SUBNET = "255.255.255.0"

# Gateway
GATEWAY = "192.168.4.1"


# =========================
# OLED CONFIG
# =========================

OLED_SCL = 22
OLED_SDA = 21

OLED_WIDTH = 128
OLED_HEIGHT = 64

# I2C speed optimal untuk SSD1306
OLED_FREQ = 400000


# =========================
# DISPLAY SESSION CONFIG
# =========================

# Tampilan 1
# AP CONTROLLER
# SSID
# IP

STATUS_INFO_DURATION = 10


# Tampilan 2
# Nodes
# Uptime
# Memory

STATUS_HEALTH_DURATION = 40


# Tampilan 3
# Jam realtime

CLOCK_DISPLAY_DURATION = 10


# =========================
# REFRESH INTERVAL CONFIG
# =========================

# Update jam real-time (detik)
CLOCK_REFRESH_INTERVAL = 1

# Update jumlah node (detik)
NODE_REFRESH_INTERVAL = 2

# Delay loop utama (detik)
DISPLAY_LOOP_DELAY = 0.1


# =========================
# DEVICE CONFIG
# =========================

DEVICE_NAME = "AP-CONTROLLER"


# =========================
# RTC CONFIG
# =========================

RTC_DEFAULT_TIME = (
    2026,  # year
    1,     # month
    1,     # day
    3,     # weekday
    0,     # hour
    0,     # minute
    0,     # second
    0      # millisecond
)


# =========================
# TIMEZONE CONFIG
# =========================

# Indonesia WIB = UTC+7
TIMEZONE_OFFSET = 7


# =========================
# SYSTEM CONFIG
# =========================

# Aktifkan log debug
DEBUG = True

# Delay setelah boot (detik)
BOOT_DELAY = 1


# =========================
# SAFETY CONFIG
# =========================

# Warning jika node mendekati penuh
NODE_WARNING_THRESHOLD = 8

# Critical jika node penuh
NODE_CRITICAL_THRESHOLD = 10


# =========================
# WATCHDOG CONFIG
# =========================

# Timeout watchdog (millisecond)

WATCHDOG_TIMEOUT = 8000


# =========================
# MEMORY CONFIG
# =========================

# Batas minimum memory sebelum warning (persen)

MEMORY_WARNING_THRESHOLD = 20


# =========================
# COMPATIBILITY (LEGACY)
# =========================

# Untuk node_monitor lama
NODE_SCAN_INTERVAL = NODE_REFRESH_INTERVAL