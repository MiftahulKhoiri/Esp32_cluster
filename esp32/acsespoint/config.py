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

# I2C Frequency
OLED_FREQ = 400000



# =========================
# SYSTEM CONFIG
# =========================

# Interval refresh layar (detik)
DISPLAY_UPDATE_INTERVAL = 1

# Interval scan node (detik)
NODE_SCAN_INTERVAL = 2

# Nama device (opsional)
DEVICE_NAME = "AP-CONTROLLER"