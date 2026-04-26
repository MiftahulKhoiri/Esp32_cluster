# =========================
# WIFI ACCESS POINT CONFIG
# =========================

# Nama WiFi Access Point
SSID = "CLUSTER-NODE"

# Password WiFi (minimal 8 karakter)
PASSWORD = "12345678"

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

# Pin I2C
OLED_SCL = 22
OLED_SDA = 21

# Resolusi display
OLED_WIDTH = 128
OLED_HEIGHT = 64

# I2C Frequency (Hz)
OLED_FREQ = 400000



# =========================
# DISPLAY CONFIG
# =========================

# Interval refresh layar (detik)
DISPLAY_UPDATE_INTERVAL = 1

# Interval scan node (detik)
NODE_SCAN_INTERVAL = 2

# Nama device (ditampilkan di OLED)
DEVICE_NAME = "AP-CONTROLLER"



# =========================
# CLOCK DISPLAY CONFIG
# =========================

# Total siklus tampilan (detik)
# contoh:
# 60 detik total
DISPLAY_CYCLE_SECONDS = 60

# Durasi tampilan jam (detik)
# contoh:
# 15 detik tampil jam
CLOCK_DISPLAY_DURATION = 15



# =========================
# RTC CONFIG
# =========================

# Default waktu RTC saat boot
# Digunakan jika RTC belum pernah diset
#
# Format:
# (year, month, day, weekday, hour, minute, second, millisecond)
#
# weekday:
# 0 = Monday
# 6 = Sunday

RTC_DEFAULT_TIME = (
    2026,   # year
    1,      # month
    1,      # day
    3,      # weekday
    0,      # hour
    0,      # minute
    0,      # second
    0       # millisecond
)



# =========================
# TIMEZONE CONFIG
# =========================

# Offset timezone dari UTC
# Indonesia WIB = UTC+7

TIMEZONE_OFFSET = 7



# =========================
# SYSTEM CONFIG
# =========================

# Aktifkan log debug
DEBUG = True

# Timeout boot (detik)
BOOT_DELAY = 1



# =========================
# SAFETY CONFIG
# =========================

# Maksimal jumlah node sebelum warning
NODE_WARNING_THRESHOLD = 8

# Maksimal jumlah node sebelum critical
NODE_CRITICAL_THRESHOLD = 10