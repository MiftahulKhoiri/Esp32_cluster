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
# LOGO BITMAP (16x16 VALID)
# =========================

logo_bitmap = bytearray([

    0x18,0x3C,
    0x7E,0xFF,
    0xDB,0x7E,
    0x3C,0x18,

    0x18,0x3C,
    0x7E,0xDB,
    0xFF,0x7E,
    0x3C,0x18

])


# =========================
# SMART TRANSITION
# =========================

def fade_transition():

    try:

        disp = get_display()

        if not disp:
            return

        for c in range(
            DEFAULT_CONTRAST,
            DEFAULT_CONTRAST - 15,
            -2
        ):

            disp.contrast(c)
            time.sleep_ms(8)

        for c in range(
            DEFAULT_CONTRAST - 15,
            DEFAULT_CONTRAST,
            2
        ):

            disp.contrast(c)
            time.sleep_ms(8)

    except:

        pass


def smart_transition(screen_name):

    global _last_screen

    if screen_name != _last_screen:

        fade_transition()

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

        time.sleep(1)

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
# GET DISPLAY
# =========================

def get_display():

    global _display

    if _display is None:

        init_display()

    return _display


# =========================
# CLEAR
# =========================

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


# =========================
# DRAW TEXT
# =========================

def draw_text(text, x, y):

    try:

        disp = get_display()

        if disp:

            disp.text(str(text), x, y)

    except:

        pass


# =========================
# UPDATE (FIXED)
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
# LOGO ANIMATION (FIXED)
# =========================

def show_logo_animation():

    try:

        print("Show logo animation")

        smart_transition("logo")

        disp = get_display()

        if not disp:
            return

        icon = framebuf.FrameBuffer(
            logo_bitmap,
            16,
            16,
            framebuf.MONO_HLSB
        )

        # ICON TURUN

        for y in range(-16, 10, 2):

            clear()

            disp.blit(icon, 56, y)

            update(True)

            time.sleep_ms(40)

        # TEXT MUNCUL

        title = DEVICE_NAME

        for i in range(len(title) + 1):

            clear_area(0, 36, 128, 12)

            draw_text(title[:i], 8, 36)

            update(True)

            time.sleep_ms(40)

        draw_text("AP CONTROLLER", 12, 50)

        update(True)

        time.sleep(1)

    except Exception as e:

        print("Logo animation error:", repr(e))


# =========================
# BOOT SCREEN
# =========================

def show_boot_screen():

    try:

        smart_transition("boot")

        clear()

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

        smart_transition("status")

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

    except:

        pass


# =========================
# CLOCK SCREEN
# =========================

def show_clock():

    try:

        smart_transition("clock")

        clear_area(0, 20, 128, 44)

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
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri",
            "Sat",
            "Sun"
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

    except:

        pass