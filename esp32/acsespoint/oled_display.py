# Import modul hardware dan display
from machine import Pin, I2C
import time

# Library driver OLED SSD1306
import ssd1306

# Ambil konfigurasi dari file config
from config import (
    OLED_SCL,
    OLED_SDA,
    OLED_WIDTH,
    OLED_HEIGHT,
    OLED_FREQ,
    DEVICE_NAME
)


# =========================
# GLOBAL
# =========================

# Objek I2C
_i2c = None

# Objek display OLED
_display = None


# =========================
# INIT DISPLAY
# =========================

def init_display():
    """
    Menginisialisasi layar OLED SSD1306 menggunakan interface I2C.
    Akan mencoba alamat 0x3C terlebih dahulu, jika gagal mencoba 0x3D.
    Mengembalikan objek display jika berhasil, atau None jika gagal.
    """

    global _i2c
    global _display

    try:
        print("Initializing OLED display")

        # Buat interface I2C
        _i2c = I2C(
            0,
            scl=Pin(OLED_SCL),
            sda=Pin(OLED_SDA),
            freq=OLED_FREQ
        )

        time.sleep(1)

        # Scan alamat I2C
        devices = _i2c.scan()

        if not devices:
            print("OLED not found")
            return None

        print("I2C devices:", devices)

        # Coba alamat umum OLED
        address = None

        if 0x3C in devices:
            address = 0x3C
        elif 0x3D in devices:
            address = 0x3D
        else:
            address = devices[0]

        # Inisialisasi display
        _display = ssd1306.SSD1306_I2C(
            OLED_WIDTH,
            OLED_HEIGHT,
            _i2c,
            addr=address
        )

        clear()

        print("OLED initialized")

        return _display

    except Exception as e:
        print("OLED init error:", e)
        return None


# =========================
# GET DISPLAY
# =========================

def get_display():
    """
    Mengembalikan objek display.
    Jika belum diinisialisasi, akan mencoba init otomatis.
    """

    global _display

    if _display is None:
        init_display()

    return _display


# =========================
# CLEAR SCREEN
# =========================

def clear():
    """
    Membersihkan layar OLED.
    """

    try:
        disp = get_display()

        if disp:
            disp.fill(0)
            disp.show()

    except Exception as e:
        print("OLED clear error:", e)


# =========================
# DRAW TEXT
# =========================

def draw_text(text, x, y):
    """
    Menampilkan teks pada posisi (x, y).
    Tidak langsung refresh layar.
    """

    try:
        disp = get_display()

        if disp:
            disp.text(text, x, y)

    except Exception as e:
        print("OLED text error:", e)


# =========================
# UPDATE SCREEN
# =========================

def update():
    """
    Menampilkan buffer ke layar OLED.
    """

    try:
        disp = get_display()

        if disp:
            disp.show()

    except Exception as e:
        print("OLED update error:", e)


# =========================
# SHOW BOOT SCREEN
# =========================

def show_boot_screen():
    """
    Menampilkan layar awal saat device boot.
    """

    try:
        clear()

        draw_text(DEVICE_NAME, 0, 0)
        draw_text("Starting...", 0, 16)

        update()

    except Exception as e:
        print("Boot screen error:", e)


# =========================
# SHOW STATUS
# =========================

def show_status(ssid, password, ip, node_count):
    """
    Menampilkan status utama pada layar OLED:
    - SSID
    - Password
    - IP address
    - Jumlah node terhubung
    """

    try:
        clear()

        draw_text("AP CONTROLLER", 0, 0)

        draw_text("SSID:", 0, 16)
        draw_text(ssid, 40, 16)

        draw_text("PASS:", 0, 26)
        draw_text(password, 40, 26)

        draw_text("IP:", 0, 40)
        draw_text(ip, 40, 40)

        draw_text("Nodes:", 0, 54)
        draw_text(str(node_count), 60, 54)

        update()

    except Exception as e:
        print("Display status error:", e)