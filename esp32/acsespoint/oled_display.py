from machine import Pin, I2C
import machine
import time

import ssd1306
import framebuf

from config import (
    OLED_SCL,
    OLED_SDA,
    OLED_WIDTH,
    OLED_HEIGHT,
    OLED_FREQ,
    DEVICE_NAME,
    RTC_DEFAULT_TIME,
    TIMEZONE_OFFSET
)

# =========================
# GLOBAL
# =========================

_i2c = None
_display = None

_last_update = 0
_last_screen = None

FRAME_INTERVAL = 250
DEFAULT_CONTRAST = 130


# =========================
# LOGO BITMAP (VALID 16x16)
# =========================

# 16 x 16 pixel = 32 byte
logo_bitmap = bytearray([

    0x18,0x18,
    0x3C,0x3C,
    0x7E,0x7E,
    0xFF,0xFF,

    0xFF,0xFF,
    0x7E,0x7E,
    0x3C,0x3C,
    0x18,0x18,

    0x18,0x18,
    0x3C,0x3C,
    0x7E,0x7E,
    0xFF,0xFF,

    0xFF,0xFF,
    0x7E,0x7E,
    0x3C,0x3C,
    0x18,0x18

])


# =========================
# SCREEN CONTROL
# =========================

def ensure_screen(screen_name):

    global _last_screen

    if screen_name != _last_screen:

        clear()

        _last_screen = screen_name


# =========================
# RTC
# =========================

def init_rtc():

    try:

        rtc = machine.RTC()

        dt = rtc.datetime()

        if dt[0] < 2024:

            rtc.datetime(RTC_DEFAULT_TIME)

            print("RTC initialized")

    except Exception as e:

        print("RTC init error:", repr(e))


# =========================
# DISPLAY INIT
# =========================

def init_display():

    global _i2c
    global _display

    try:

        print("Initializing OLED")

        init_rtc()

        _i2c = I2C(
            0,
            scl=Pin(OLED_SCL),
            sda=Pin(OLED_SDA),
            freq=OLED_FREQ
        )

        time.sleep(0.5)

        devices = _i2c.scan()

        if not devices:

            print("OLED not found")

            return None

        if 0x3C in devices:
            address = 0x3C
        elif 0x3D in devices:
            address = 0x3D
        else:
            address = devices[0]

        _display = ssd1306.SSD1306_I2C(
            OLED_WIDTH,
            OLED_HEIGHT,
            _i2c,
            addr=address
        )

        _display.contrast(DEFAULT_CONTRAST)

        clear()
        update(True)

        print("OLED ready")

        return _display

    except Exception as e:

        print("OLED init error:", repr(e))

        return None


# =========================
# BASIC DRAW
# =========================

def get_display():

    global _display

    if _display is None:

        init_display()

    return _display


def clear():

    try:

        disp = get_display()

        if disp:

            disp.fill(0)

    except:
        pass


def clear_area(x, y, w, h):

    try:

        disp = get_display()

        if disp:

            disp.fill_rect(x, y, w, h, 0)

    except:
        pass


def draw_text(text, x, y):

    try:

        disp = get_display()

        if disp:

            disp.text(str(text), x, y)

    except:
        pass


# =========================
# UPDATE
# =========================

def update(force=False):

    global _last_update

    try:

        disp = get_display()

        if not disp:
            return

        now = time.ticks_ms()

        if not force:

            if time.ticks_diff(
                now,
                _last_update
            ) < FRAME_INTERVAL:

                return

        disp.show()

        _last_update = now

    except:
        pass


# =========================
# LOGO ANIMATION
# =========================

def show_logo_animation():

    try:

        print("Show logo animation")

        ensure_screen("logo")

        disp = get_display()

        icon = framebuf.FrameBuffer(
            logo_bitmap,
            16,
            16,
            framebuf.MONO_HLSB
        )

        # gerakan turun (smooth)

        for y in range(-16, 10):

            clear()

            disp.blit(icon, 56, y)

            update(True)

            time.sleep_ms(50)

        title = DEVICE_NAME

        for i in range(len(title) + 1):

            clear_area(0, 36, 128, 12)

            draw_text(title[:i], 8, 36)

            update(True)

            time.sleep_ms(45)

        draw_text("AP CONTROLLER", 12, 50)

        update(True)

        time.sleep(1.5)

    except Exception as e:

        print("Logo animation error:", repr(e))


# =========================
# BOOT SCREEN
# =========================

def show_boot_screen():

    try:

        ensure_screen("boot")

        draw_text(DEVICE_NAME, 0, 0)

        draw_text("Starting...", 0, 16)

        update(True)

    except:
        pass


# =========================
# STATUS SCREEN
# =========================

def show_status(ssid, password, ip, node_count):

    try:

        ensure_screen("status")

        clear_area(0, 0, 128, 64)

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

        print("Status error:", repr(e))


# =========================
# TIME
# =========================

def get_current_time():

    try:

        rtc = machine.RTC()

        dt = rtc.datetime()

        year = dt[0]
        month = dt[1]
        day = dt[2]
        weekday = dt[3]

        hour = dt[4] + TIMEZONE_OFFSET
        minute = dt[5]
        second = dt[6]

        if hour >= 24:
            hour -= 24

        return (
            year,
            month,
            day,
            weekday,
            hour,
            minute,
            second
        )

    except:

        return (0,0,0,0,0,0,0)


# =========================
# CLOCK SCREEN
# =========================

def show_clock():

    try:

        ensure_screen("clock")

        clear_area(0, 0, 128, 64)

        (
            year,
            month,
            day,
            weekday,
            hour,
            minute,
            second
        ) = get_current_time()

        days = [
            "Mon","Tue","Wed",
            "Thu","Fri","Sat","Sun"
        ]

        if weekday < len(days):
            day_name = days[weekday]
        else:
            day_name = "Day"

        time_str = "{:02d}:{:02d}:{:02d}".format(
            hour,
            minute,
            second
        )

        date_str = "{:02d}/{:02d}/{:04d}".format(
            day,
            month,
            year
        )

        draw_text("CLOCK", 0, 0)

        draw_text(time_str, 0, 20)

        draw_text(day_name, 0, 40)

        draw_text(date_str, 0, 52)

        update()

    except Exception as e:

        print("Clock error:", repr(e))