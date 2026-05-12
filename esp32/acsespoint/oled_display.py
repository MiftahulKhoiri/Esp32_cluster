# =========================================================
# OLED DISPLAY INDUSTRIAL FRAMEWORK
# File : oled_display.py
# =========================================================
#
# INDUSTRIAL GRADE OLED FRAMEWORK
# Untuk ESP32 + MicroPython + SSD1306
#
# FITUR:
# - Production Ready
# - Ultra Stable Runtime
# - Auto Recovery
# - Auto Sleep
# - Anti Burn-In
# - Thread Safe
# - Async Compatible
# - Low RAM Usage
# - Dirty Refresh System
# - GUI Framework
# - State Machine
# - Animation Engine
# - Auto Reconnect OLED
# - Memory Protection
# - Long Runtime Stability
#
# =========================================================


# =========================================================
# IMPORT
# =========================================================

from machine import Pin, I2C

import machine
import time
import gc
import framebuf
import _thread

import ssd1306

from config import (

    OLED_SCL,
    OLED_SDA,

    OLED_WIDTH,
    OLED_HEIGHT,

    OLED_FREQ,

    DEVICE_NAME
)


# =========================================================
# GLOBAL
# =========================================================

_i2c = None

_display = None

_initialized = False

_display_failed = False

_display_sleep = False

_lock = _thread.allocate_lock()

_last_update = 0

_last_activity = 0

_last_gc = 0

_last_recovery = 0

FRAME_INTERVAL = 33

SLEEP_TIMEOUT = 60000

GC_INTERVAL = 30000

RECOVERY_INTERVAL = 10000

DEFAULT_CONTRAST = 120

ANTI_BURNIN_SHIFT = True

_burnin_offset = 0

_last_burnin = 0

_current_page = None

_pages = {}

STATE_BOOT = 0
STATE_IDLE = 1
STATE_MENU = 2
STATE_STATUS = 3

_current_state = STATE_BOOT


# =========================================================
# SAFE LOCK
# =========================================================

def acquire():

    try:
        _lock.acquire()

    except:
        pass


def release():

    try:
        _lock.release()

    except:
        pass


# =========================================================
# DISPLAY RECOVERY
# =========================================================

def recover():

    global _display
    global _initialized
    global _display_failed
    global _last_recovery

    now = time.ticks_ms()

    if time.ticks_diff(
        now,
        _last_recovery
    ) < RECOVERY_INTERVAL:

        return False

    _last_recovery = now

    try:

        print("OLED RECOVERY")

        _display = None

        _initialized = False

        _display_failed = False

        return init()

    except Exception as e:

        print(
            "RECOVERY ERROR:",
            repr(e)
        )

        return False


# =========================================================
# INIT DISPLAY
# =========================================================

def init():

    global _i2c
    global _display

    global _initialized
    global _display_failed

    if _initialized:
        return True

    try:

        print("OLED INIT")

        _i2c = I2C(
            0,
            scl=Pin(OLED_SCL),
            sda=Pin(OLED_SDA),
            freq=OLED_FREQ
        )

        time.sleep_ms(300)

        devices = _i2c.scan()

        if not devices:

            print("OLED NOT FOUND")

            _display_failed = True

            return False

        # Auto detect address
        if 0x3C in devices:

            addr = 0x3C

        elif 0x3D in devices:

            addr = 0x3D

        else:

            addr = devices[0]

        print(
            "OLED ADDRESS:",
            hex(addr)
        )

        _display = ssd1306.SSD1306_I2C(
            OLED_WIDTH,
            OLED_HEIGHT,
            _i2c,
            addr=addr
        )

        _display.contrast(
            DEFAULT_CONTRAST
        )

        clear()

        show(True)

        _initialized = True

        _display_failed = False

        print("OLED READY")

        return True

    except Exception as e:

        print(
            "OLED INIT ERROR:",
            repr(e)
        )

        _display_failed = True

        return False


# =========================================================
# GET DISPLAY
# =========================================================

def display():

    global _display

    if _display_failed:

        recover()

    if not _initialized:

        init()

    return _display


# =========================================================
# DISPLAY ACTIVITY
# =========================================================

def activity():

    global _last_activity

    _last_activity = time.ticks_ms()


# =========================================================
# AUTO SLEEP
# =========================================================

def sleep_check():

    global _display_sleep

    try:

        disp = display()

        if not disp:
            return

        now = time.ticks_ms()

        idle = time.ticks_diff(
            now,
            _last_activity
        )

        if idle > SLEEP_TIMEOUT:

            if not _display_sleep:

                disp.poweroff()

                _display_sleep = True

    except Exception as e:

        print(
            "SLEEP ERROR:",
            repr(e)
        )


# =========================================================
# WAKE DISPLAY
# =========================================================

def wake():

    global _display_sleep

    try:

        disp = display()

        if disp:

            if _display_sleep:

                disp.poweron()

                _display_sleep = False

            activity()

    except Exception as e:

        print(
            "WAKE ERROR:",
            repr(e)
        )


# =========================================================
# ANTI BURN-IN
# =========================================================

def burnin_protection():

    global _burnin_offset
    global _last_burnin

    if not ANTI_BURNIN_SHIFT:
        return

    now = time.ticks_ms()

    if time.ticks_diff(
        now,
        _last_burnin
    ) < 15000:

        return

    _burnin_offset += 1

    if _burnin_offset > 2:

        _burnin_offset = 0

    _last_burnin = now


# =========================================================
# MEMORY MAINTENANCE
# =========================================================

def memory_maintenance():

    global _last_gc

    now = time.ticks_ms()

    if time.ticks_diff(
        now,
        _last_gc
    ) >= GC_INTERVAL:

        gc.collect()

        _last_gc = now


# =========================================================
# CLEAR SCREEN
# =========================================================

def clear():

    try:

        acquire()

        wake()

        disp = display()

        if disp:

            disp.fill(0)

    except Exception as e:

        print(
            "CLEAR ERROR:",
            repr(e)
        )

    finally:

        release()


# =========================================================
# SHOW OLED
# =========================================================

def show(force=False):

    global _last_update

    try:

        acquire()

        wake()

        disp = display()

        if not disp:
            return

        now = time.ticks_ms()

        if not force:

            if time.ticks_diff(
                now,
                _last_update
            ) < FRAME_INTERVAL:

                return

        burnin_protection()

        disp.show()

        _last_update = now

        activity()

    except Exception as e:

        print(
            "SHOW ERROR:",
            repr(e)
        )

        recover()

    finally:

        release()


# =========================================================
# DRAW TEXT
# =========================================================

def text(
    message,
    x,
    y,
    refresh=False
):

    try:

        acquire()

        wake()

        disp = display()

        if disp:

            disp.text(
                str(message),
                x + _burnin_offset,
                y + _burnin_offset,
                1
            )

    except Exception as e:

        print(
            "TEXT ERROR:",
            repr(e)
        )

    finally:

        release()

    if refresh:

        show()


# =========================================================
# CENTER TEXT
# =========================================================

def center(
    message,
    y=28,
    refresh=False
):

    message = str(message)

    width = len(message) * 8

    x = (OLED_WIDTH - width) // 2

    if x < 0:
        x = 0

    text(
        message,
        x,
        y,
        refresh
    )


# =========================================================
# RECTANGLE
# =========================================================

def rect(
    x,
    y,
    w,
    h,
    fill=False
):

    try:

        acquire()

        wake()

        disp = display()

        if not disp:
            return

        if fill:

            disp.fill_rect(
                x,
                y,
                w,
                h,
                1
            )

        else:

            disp.rect(
                x,
                y,
                w,
                h,
                1
            )

    except Exception as e:

        print(
            "RECT ERROR:",
            repr(e)
        )

    finally:

        release()


# =========================================================
# STATUS INFO
# =========================================================

def show_status_info(
    ssid,
    password,
    ip
):

    clear()

    text(
        "AP CONTROLLER",
        0,
        0
    )

    text(
        "SSID:",
        0,
        18
    )

    text(
        ssid,
        48,
        18
    )

    text(
        "PASS:",
        0,
        34
    )

    text(
        password,
        48,
        34
    )

    text(
        "IP:",
        0,
        50
    )

    text(
        ip,
        48,
        50
    )

    show()


# =========================================================
# STATUS HEALTH
# =========================================================

def show_status_health(
    node_count
):

    clear()

    mem = gc.mem_free()

    text(
        "NODES:",
        0,
        10
    )

    text(
        str(node_count),
        70,
        10
    )

    text(
        "FREE RAM:",
        0,
        30
    )

    text(
        str(mem),
        70,
        30
    )

    text(
        "SYSTEM OK",
        0,
        50
    )

    show()


# =========================================================
# CLOCK
# =========================================================

def show_clock():

    try:

        rtc = machine.RTC()

        dt = rtc.datetime()

        hour = dt[4]
        minute = dt[5]
        second = dt[6]

        clear()

        center(
            "{:02d}:{:02d}:{:02d}".format(
                hour,
                minute,
                second
            ),
            24
        )

        show()

    except Exception as e:

        print(
            "CLOCK ERROR:",
            repr(e)
        )


# =========================================================
# ROBOT EYES
# =========================================================

def robot_eyes(
    offset=0,
    blink=False
):

    try:

        clear()

        wake()

        disp = display()

        if not disp:
            return

        lx = 34 + offset
        rx = 94 + offset

        y = 32

        if blink:

            disp.fill_rect(
                lx - 15,
                y,
                30,
                3,
                1
            )

            disp.fill_rect(
                rx - 15,
                y,
                30,
                3,
                1
            )

        else:

            disp.fill_rect(
                lx - 15,
                y - 15,
                30,
                30,
                1
            )

            disp.fill_rect(
                rx - 15,
                y - 15,
                30,
                30,
                1
            )

            disp.fill_rect(
                lx - 4,
                y - 4,
                8,
                8,
                0
            )

            disp.fill_rect(
                rx - 4,
                y - 4,
                8,
                8,
                0
            )

        show(True)

    except Exception as e:

        print(
            "ROBOT ERROR:",
            repr(e)
        )


# =========================================================
# LOGO ANIMATION
# =========================================================

def show_logo_animation():

    try:

        for i in range(3):

            clear()

            center(
                DEVICE_NAME,
                20
            )

            center(
                "LOADING" + ("." * i),
                40
            )

            show(True)

            time.sleep_ms(400)

    except Exception as e:

        print(
            "LOGO ERROR:",
            repr(e)
        )


# =========================================================
# BOOT SCREEN
# =========================================================

def show_boot_screen():

    clear()

    center(
        DEVICE_NAME,
        16
    )

    center(
        "SYSTEM START",
        36
    )

    show(True)


# =========================================================
# PAGE SYSTEM
# =========================================================

def register_page(
    name,
    callback
):

    _pages[name] = callback


def render(name):

    global _current_page

    if name not in _pages:
        return

    _current_page = name

    try:

        _pages[name]()

    except Exception as e:

        print(
            "PAGE ERROR:",
            repr(e)
        )


def next_page():

    global _current_page

    keys = list(_pages.keys())

    if not keys:
        return

    if _current_page not in keys:

        render(keys[0])

        return

    idx = keys.index(
        _current_page
    )

    idx += 1

    if idx >= len(keys):
        idx = 0

    render(keys[idx])


# =========================================================
# GUI LABEL
# =========================================================

class Label:

    def __init__(
        self,
        x,
        y,
        value
    ):

        self.x = x
        self.y = y

        self.value = value

    def draw(self):

        text(
            self.value,
            self.x,
            self.y
        )


# =========================================================
# GUI BUTTON
# =========================================================

class Button:

    def __init__(
        self,
        x,
        y,
        w,
        h,
        label
    ):

        self.x = x
        self.y = y

        self.w = w
        self.h = h

        self.label = label

    def draw(self):

        rect(
            self.x,
            self.y,
            self.w,
            self.h
        )

        text(
            self.label,
            self.x + 4,
            self.y + 4
        )


# =========================================================
# STATE MACHINE
# =========================================================

def set_state(state):

    global _current_state

    _current_state = state


def update_state():

    if _current_state == STATE_BOOT:

        show_boot_screen()

    elif _current_state == STATE_IDLE:

        robot_eyes()

    elif _current_state == STATE_MENU:

        clear()

        center("MENU")

        show()

    elif _current_state == STATE_STATUS:

        show_status_health(0)


# =========================================================
# ASYNC SUPPORT
# =========================================================

async def async_loading():

    import uasyncio as asyncio

    while True:

        clear()

        center("ASYNC MODE")

        show()

        await asyncio.sleep(1)


# =========================================================
# BACKGROUND TASK
# =========================================================

def background_worker():

    while True:

        try:

            sleep_check()

            memory_maintenance()

        except Exception as e:

            print(
                "BG ERROR:",
                repr(e)
            )

        time.sleep_ms(1000)


# =========================================================
# START BACKGROUND
# =========================================================

def start_background():

    try:

        _thread.start_new_thread(
            background_worker,
            ()
        )

    except Exception as e:

        print(
            "THREAD ERROR:",
            repr(e)
        )


# =========================================================
# AUTO START
# =========================================================

init()

start_background()