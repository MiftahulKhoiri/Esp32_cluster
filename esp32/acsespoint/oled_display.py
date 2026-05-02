# Import modul hardware dan display
from machine import Pin, I2C
import machine
import time

import ssd1306

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

# interval minimal refresh (ms)
UPDATE_INTERVAL = 500


# =========================
# FADE TRANSITION
# =========================

def fade_transition():

    try:

        disp = get_display()

        if not disp:
            return

        # redup
        for c in range(255, 150, -15):

            disp.contrast(c)
            time.sleep_ms(10)

        # terang
        for c in range(150, 256, 15):

            disp.contrast(c)
            time.sleep_ms(10)

    except:

        pass


# =========================
# INIT RTC
# =========================

def init_rtc():

    try:

        rtc = machine.RTC()

        dt = rtc.datetime()

        if dt[0] < 2024:

            rtc.datetime(RTC_DEFAULT_TIME)

            print("RTC initialized")

    except Exception as e:

        print("RTC init error:", e)


# =========================
# INIT DISPLAY
# =========================

def init_display():

    global _i2c
    global _display

    try:

        print("Initializing OLED display")

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

        print("I2C devices:", devices)

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

        clear()

        update()

        print("OLED initialized")

        return _display

    except Exception as e:

        print("OLED init error:", e)

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
# CLEAR SCREEN
# =========================

def clear():

    try:

        disp = get_display()

        if disp:

            disp.fill(0)

    except Exception as e:

        print("OLED clear error:", e)


# =========================
# DRAW TEXT
# =========================

def draw_text(text, x, y):

    try:

        disp = get_display()

        if disp:

            disp.text(str(text), x, y)

    except Exception as e:

        print("OLED text error:", e)


# =========================
# SAFE UPDATE (ANTI FLICKER)
# =========================

def update():

    global _last_update

    try:

        disp = get_display()

        if not disp:

            return

        now = time.ticks_ms()

        if time.ticks_diff(now, _last_update) < UPDATE_INTERVAL:

            return

        disp.show()

        _last_update = now

    except Exception as e:

        print("OLED update error:", e)


# =========================
# SHOW BOOT SCREEN
# =========================

def show_boot_screen():

    try:

        fade_transition()

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

    try:

        fade_transition()

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


# =========================
# GET CURRENT TIME
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

        return (0, 0, 0, 0, 0, 0, 0)


# =========================
# SHOW CLOCK
# =========================

def show_clock():

    try:

        clear()

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

    except Exception as e:

        print("Clock display error:", e)