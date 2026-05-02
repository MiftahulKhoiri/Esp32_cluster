from machine import Pin, I2C
import machine
import time
import gc

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
    TIMEZONE_OFFSET,
    NODE_WARNING_THRESHOLD,
    NODE_CRITICAL_THRESHOLD
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

_boot_time = time.ticks_ms()


# =========================
# LOGO BITMAP
# =========================

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
# UPTIME
# =========================

def get_uptime():

    seconds = time.ticks_diff(
        time.ticks_ms(),
        _boot_time
    ) // 1000

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return "{:02d}:{:02d}".format(
        hours,
        minutes
    )


# =========================
# MEMORY
# =========================

def get_memory_percent():

    free = gc.mem_free()

    total = gc.mem_alloc() + free

    percent = int(
        (free / total) * 100
    )

    return percent


# =========================
# NODE STATUS
# =========================

def get_node_status(count):

    if count >= NODE_CRITICAL_THRESHOLD:

        return "FULL"

    elif count >= NODE_WARNING_THRESHOLD:

        return "WARN"

    else:

        return "OK"


# =========================
# STATUS INFO (10 detik)
# =========================

def show_status_info(ssid, ip):

    try:

        ensure_screen("status_info")

        clear_area(0, 0, 128, 64)

        draw_text("AP CONTROLLER", 0, 0)

        draw_text("SSID:", 0, 20)
        draw_text(ssid, 40, 20)

        draw_text("IP:", 0, 40)
        draw_text(ip, 40, 40)

        update()

    except Exception as e:

        print("Status info error:", repr(e))


# =========================
# STATUS HEALTH (40 detik)
# =========================

def show_status_health(node_count):

    try:

        ensure_screen("status_health")

        clear_area(0, 0, 128, 64)

        status = get_node_status(node_count)

        uptime = get_uptime()

        mem = get_memory_percent()

        draw_text("Nodes:", 0, 10)
        draw_text(str(node_count), 60, 10)

        draw_text(status, 95, 10)

        draw_text("Up:", 0, 30)
        draw_text(uptime, 60, 30)

        draw_text("Mem:", 0, 50)
        draw_text(str(mem) + "%", 60, 50)

        update()

    except Exception as e:

        print("Status health error:", repr(e))


# =========================
# CLOCK
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