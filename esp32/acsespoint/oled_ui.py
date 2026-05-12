# =========================================================
# OLED UI FRAMEWORK
# Untuk SSD1306 + MicroPython
# =========================================================
#
# Author  : ChatGPT
# Version : Production Ready
#
# Fitur:
# - Text biasa
# - Text tengah
# - Multiline
# - Splash screen
# - Loading animation
# - Progress bar
# - Notification popup
# - Scroll text
# - Robot eyes
# - Frame / border
# - Status bar
# - Logo bitmap
# - Clear screen
#
# Kompatibel:
# - ESP32
# - ESP8266
# - Raspberry Pi Pico
#
# Dependency:
# - ssd1306.py
#
# =========================================================


# =========================================================
# IMPORT
# =========================================================

from machine import Pin, I2C

from ssd1306 import SSD1306_I2C

import time


# =========================================================
# KONFIGURASI I2C
# =========================================================

I2C_SCL_PIN = 22

I2C_SDA_PIN = 21

I2C_FREQ = 400000


# =========================================================
# INISIALISASI I2C
# =========================================================

i2c = I2C(
    0,
    scl=Pin(I2C_SCL_PIN),
    sda=Pin(I2C_SDA_PIN),
    freq=I2C_FREQ
)


# =========================================================
# INISIALISASI OLED
# =========================================================

oled = SSD1306_I2C(
    128,
    64,
    i2c
)


# =========================================================
# CLEAR SCREEN
# =========================================================

def clear():

    oled.fill(0)

    oled.show()


# =========================================================
# TEXT BIASA
# =========================================================

def text(
    pesan,
    x=0,
    y=0,
    clear_screen=True
):

    if clear_screen:
        oled.fill(0)

    oled.text(
        str(pesan),
        x,
        y,
        1
    )

    oled.show()


# =========================================================
# TEXT TENGAH
# =========================================================

def center_text(
    pesan,
    y=28,
    clear_screen=True
):

    if clear_screen:
        oled.fill(0)

    pesan = str(pesan)

    # Estimasi lebar karakter
    width = len(pesan) * 8

    x = (128 - width) // 2

    if x < 0:
        x = 0

    oled.text(
        pesan,
        x,
        y,
        1
    )

    oled.show()


# =========================================================
# TEXT MULTILINE
# =========================================================

def multiline(
    isi,
    clear_screen=True
):

    if clear_screen:
        oled.fill(0)

    lines = str(isi).split("\n")

    y = 0

    for line in lines:

        oled.text(
            line,
            0,
            y,
            1
        )

        y += 10

        if y > 54:
            break

    oled.show()


# =========================================================
# SPLASH SCREEN
# =========================================================

def splash(
    pesan,
    delay=2
):

    center_text(pesan)

    time.sleep(delay)

    clear()


# =========================================================
# FRAME / BORDER
# =========================================================

def frame():

    oled.rect(
        0,
        0,
        128,
        64,
        1
    )

    oled.show()


# =========================================================
# STATUS BAR
# =========================================================

def status_bar(
    kiri="READY",
    kanan="OK"
):

    oled.fill_rect(
        0,
        0,
        128,
        10,
        1
    )

    oled.text(
        kiri,
        2,
        1,
        0
    )

    right_x = 128 - (len(kanan) * 8)

    oled.text(
        kanan,
        right_x,
        1,
        0
    )

    oled.show()


# =========================================================
# PROGRESS BAR
# =========================================================

def progress(
    persen,
    text_loading="Loading..."
):

    if persen < 0:
        persen = 0

    if persen > 100:
        persen = 100

    oled.fill(0)

    center_text(
        text_loading,
        10,
        False
    )

    # Border progress
    oled.rect(
        14,
        30,
        100,
        12,
        1
    )

    # Isi progress
    width = int((persen / 100) * 96)

    oled.fill_rect(
        16,
        32,
        width,
        8,
        1
    )

    # Persentase
    center_text(
        str(persen) + "%",
        50,
        False
    )

    oled.show()


# =========================================================
# ANIMASI LOADING TITIK
# =========================================================

def loading(
    pesan="Loading",
    durasi=3
):

    start = time.time()

    while (time.time() - start) < durasi:

        for titik in range(4):

            oled.fill(0)

            center_text(
                pesan + ("." * titik),
                28,
                False
            )

            oled.show()

            time.sleep(0.4)


# =========================================================
# NOTIFICATION POPUP
# =========================================================

def popup(
    judul,
    pesan,
    delay=2
):

    oled.fill(0)

    oled.rect(
        10,
        10,
        108,
        44,
        1
    )

    oled.fill_rect(
        10,
        10,
        108,
        12,
        1
    )

    oled.text(
        judul,
        15,
        12,
        0
    )

    oled.text(
        pesan,
        15,
        32,
        1
    )

    oled.show()

    time.sleep(delay)


# =========================================================
# SCROLL TEXT
# =========================================================

def scroll_text(
    pesan,
    speed=0.03
):

    pesan = "   " + str(pesan)

    text_width = len(pesan) * 8

    for x in range(128, -text_width, -1):

        oled.fill(0)

        oled.text(
            pesan,
            x,
            28,
            1
        )

        oled.show()

        time.sleep(speed)


# =========================================================
# ROBOT EYES
# =========================================================

def robot_eyes(
    blink=False,
    offset=0
):

    oled.fill(0)

    left_x = 34 + offset

    right_x = 94 + offset

    y = 32

    if blink:

        oled.fill_rect(
            left_x - 15,
            y,
            30,
            3,
            1
        )

        oled.fill_rect(
            right_x - 15,
            y,
            30,
            3,
            1
        )

    else:

        oled.fill_rect(
            left_x - 15,
            y - 15,
            30,
            30,
            1
        )

        oled.fill_rect(
            right_x - 15,
            y - 15,
            30,
            30,
            1
        )

        oled.fill_rect(
            left_x - 4,
            y - 4,
            8,
            8,
            0
        )

        oled.fill_rect(
            right_x - 4,
            y - 4,
            8,
            8,
            0
        )

    oled.show()


# =========================================================
# ANIMASI ROBOT
# =========================================================

def robot_animation():

    robot_eyes(offset=-5)

    time.sleep(0.5)

    robot_eyes(offset=0)

    time.sleep(0.5)

    robot_eyes(offset=5)

    time.sleep(0.5)

    robot_eyes(blink=True)

    time.sleep(0.2)

    robot_eyes(offset=0)


# =========================================================
# LOGO BITMAP
# =========================================================
#
# Gunakan image2cpp:
# https://javl.github.io/image2cpp/
#
# Format:
# - Monochrome
# - Horizontal byte
#
# =========================================================

def logo(bitmap, width, height):

    oled.fill(0)

    oled.blit(
        bitmap,
        (128 - width) // 2,
        (64 - height) // 2
    )

    oled.show()


# =========================================================
# DEMO SEMUA FITUR
# =========================================================

def demo():

    splash("OLED UI", 2)

    loading("BOOTING", 3)

    for i in range(101):

        progress(i)

        time.sleep(0.02)

    popup(
        "SYSTEM",
        "READY",
        2
    )

    scroll_text(
        "Selamat datang di OLED Framework MicroPython"
    )

    for i in range(3):

        robot_animation()

        time.sleep(0.5)

    multiline(
        "Framework OLED\nProduction Ready\nESP32 + SSD1306"
    )