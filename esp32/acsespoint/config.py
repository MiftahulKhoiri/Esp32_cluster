# =========================
# WIFI ACCESS POINT CONFIG
# =========================

SSID = "CLUSTER-NODE"

PASSWORD = "root123"

CHANNEL = 6

MAX_CLIENTS = 10

AP_IP = "192.168.4.1"

SUBNET = "255.255.255.0"

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

# Durasi tampilan STATUS (detik)
STATUS_DISPLAY_DURATION = 60

# Durasi tampilan CLOCK (detik)
CLOCK_DISPLAY_DURATION = 30


# =========================
# REFRESH INTERVAL CONFIG
# =========================

# Update jam real-time
CLOCK_REFRESH_INTERVAL = 1

# Update jumlah node
NODE_REFRESH_INTERVAL = 2

# Delay loop utama
DISPLAY_LOOP_DELAY = 0.1


# =========================
# DEVICE CONFIG
# =========================

DEVICE_NAME = "AP-CONTROLLER"


# =========================
# RTC CONFIG
# =========================

RTC_DEFAULT_TIME = (
    2026,
    1,
    1,
    3,
    0,
    0,
    0,
    0
)


# =========================
# TIMEZONE CONFIG
# =========================

TIMEZONE_OFFSET = 7


# =========================
# SYSTEM CONFIG
# =========================

DEBUG = True

BOOT_DELAY = 1


# =========================
# SAFETY CONFIG
# =========================

NODE_WARNING_THRESHOLD = 8

NODE_CRITICAL_THRESHOLD = 10

# =========================
# REFRESH INTERVAL CONFIG
# =========================

CLOCK_REFRESH_INTERVAL = 1

NODE_REFRESH_INTERVAL = 2

DISPLAY_LOOP_DELAY = 0.1


# =========================
# COMPATIBILITY (LEGACY)
# =========================

NODE_SCAN_INTERVAL = NODE_REFRESH_INTERVAL