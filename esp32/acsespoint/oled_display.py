
# =========================================================
# OLED DISPLAY INDUSTRIAL FRAMEWORK
# File : oled_display.py
# Target:
# - ESP32
# - MicroPython
# - SSD1306
#
# FITUR:
# - Production Ready
# - Industrial Grade Structure
# - Ultra Low RAM
# - Async Compatible
# - Multitasking Safe
# - Auto Sleep
# - Anti Burn-In
# - Partial Refresh
# - Page Rendering
# - Mini GUI Framework
# - Smooth Animation
# - State Machine UI
#
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

_lock = _thread.allocate_lock()

_last_update = 0
_last_activity = 0

_current_page = None

FRAME_INTERVAL = 33
SLEEP_TIMEOUT = 60000

DEFAULT_CONTRAST = 120

ANTI_BURNIN_SHIFT = True

_burnin_offset = 0
_last_burnin = 0

DIRTY_X = 0
DIRTY_Y = 0
DIRTY_W = OLED_WIDTH
DIRTY_H = OLED_HEIGHT

# =========================================================
# PAGE SYSTEM
# =========================================================

_pages = {}

# =========================================================
# SAFE LOCK
# =========================================================

def acquire():
    _lock.acquire()

def release():
    _lock.release()

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

        _i2c = I2C(
            0,
            scl=Pin(OLED_SCL),
            sda=Pin(OLED_SDA),
            freq=OLED_FREQ
        )

        time.sleep_ms(200)

        devices = _i2c.scan()

        if not devices:
            print("OLED NOT FOUND")
            _display_failed = True
            return False

        if 0x3C in devices:
            addr = 0x3C
        elif 0x3D in devices:
            addr = 0x3D
        else:
            addr = devices[0]

        _display = ssd1306.SSD1306_I2C(
            OLED_WIDTH,
            OLED_HEIGHT,
            _i2c,
            addr=addr
        )

        _display.contrast(DEFAULT_CONTRAST)

        clear()
        show(force=True)

        _initialized = True

        print("OLED READY")

        return True

    except Exception as e:

        print("OLED INIT ERROR:", repr(e))

        _display_failed = True

        return False

# =========================================================
# GET DISPLAY
# =========================================================

def display():

    if _display_failed:
        return None

    if not _initialized:
        init()

    return _display

# =========================================================
# ACTIVITY
# =========================================================

def activity():

    global _last_activity

    _last_activity = time.ticks_ms()

# =========================================================
# AUTO SLEEP
# =========================================================

def sleep_check():

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
            disp.poweroff()

    except:
        pass

# =========================================================
# WAKE DISPLAY
# =========================================================

def wake():

    try:

        disp = display()

        if disp:

            disp.poweron()

            activity()

    except:
        pass

# =========================================================
# ANTI BURN-IN
# =========================================================

def burnin_protection():

    global _burnin_offset
    global _last_burnin

    if not ANTI_BURNIN_SHIFT:
        return

    now = time.ticks_ms()

    if time.ticks_diff(now, _last_burnin) < 15000:
        return

    _burnin_offset += 1

    if _burnin_offset > 2:
        _burnin_offset = 0

    _last_burnin = now

# =========================================================
# CLEAR
# =========================================================

def clear():

    try:

        acquire()

        disp = display()

        if disp:

            disp.fill(0)

            mark_dirty(
                0,
                0,
                OLED_WIDTH,
                OLED_HEIGHT
            )

    finally:
        release()

# =========================================================
# DIRTY RECTANGLE
# =========================================================

def mark_dirty(x, y, w, h):

    global DIRTY_X
    global DIRTY_Y
    global DIRTY_W
    global DIRTY_H

    DIRTY_X = x
    DIRTY_Y = y
    DIRTY_W = w
    DIRTY_H = h

# =========================================================
# SHOW
# =========================================================

def show(force=False):

    global _last_update

    try:

        acquire()

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

    finally:
        release()

# =========================================================
# DRAW TEXT
# =========================================================

def text(msg, x, y, refresh=False):

    try:

        acquire()

        disp = display()

        if disp:

            disp.text(
                str(msg),
                x + _burnin_offset,
                y + _burnin_offset,
                1
            )

            mark_dirty(x, y, 80, 10)

    finally:
        release()

    if refresh:
        show()

# =========================================================
# CENTER TEXT
# =========================================================

def center(msg, y=28, refresh=False):

    msg = str(msg)

    width = len(msg) * 8

    x = (OLED_WIDTH - width) // 2

    if x < 0:
        x = 0

    text(
        msg,
        x,
        y,
        refresh
    )

# =========================================================
# RECTANGLE
# =========================================================

def rect(x, y, w, h, fill=False):

    try:

        acquire()

        disp = display()

        if not disp:
            return

        if fill:
            disp.fill_rect(x, y, w, h, 1)
        else:
            disp.rect(x, y, w, h, 1)

        mark_dirty(x, y, w, h)

    finally:
        release()

# =========================================================
# LOADING
# =========================================================

def loading(title="Loading", duration=3):

    start = time.time()

    while (time.time() - start) < duration:

        for i in range(4):

            clear()

            center(
                title + ("." * i)
            )

            show(True)

            time.sleep_ms(250)

            gc.collect()

# =========================================================
# PROGRESS BAR
# =========================================================

def progress(percent, title="Loading"):

    if percent < 0:
        percent = 0

    if percent > 100:
        percent = 100

    clear()

    center(title, 10)

    rect(14, 30, 100, 12)

    width = int((percent / 100) * 96)

    rect(
        16,
        32,
        width,
        8,
        True
    )

    center(
        str(percent) + "%",
        50
    )

    show(True)

# =========================================================
# CYBERPUNK DASHBOARD
# =========================================================

def cyberpunk_dashboard(
    cpu=0,
    mem=0,
    net=0
):

    clear()

    text("SYS CORE", 0, 0)

    text("CPU", 0, 18)
    rect(30, 18, cpu, 6, True)

    text("MEM", 0, 34)
    rect(30, 34, mem, 6, True)

    text("NET", 0, 50)
    rect(30, 50, net, 6, True)

    show()

# =========================================================
# ROBOT EYES
# =========================================================

def robot_eyes(offset=0, blink=False):

    clear()

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

# =========================================================
# SMOOTH ANIMATION
# =========================================================

def smooth_move():

    for i in range(-6, 7):

        robot_eyes(i)

        time.sleep_ms(30)

    for i in range(6, -7, -1):

        robot_eyes(i)

        time.sleep_ms(30)

# =========================================================
# PAGE SYSTEM
# =========================================================

def register_page(name, callback):

    _pages[name] = callback

# =========================================================
# RENDER PAGE
# =========================================================

def render(name):

    global _current_page

    if name not in _pages:
        return

    _current_page = name

    _pages[name]()

# =========================================================
# NEXT PAGE
# =========================================================

def next_page():

    global _current_page

    keys = list(_pages.keys())

    if not keys:
        return

    if _current_page not in keys:

        render(keys[0])

        return

    idx = keys.index(_current_page)

    idx += 1

    if idx >= len(keys):
        idx = 0

    render(keys[idx])

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
# GUI LABEL
# =========================================================

class Label:

    def __init__(
        self,
        x,
        y,
        text_value
    ):

        self.x = x
        self.y = y

        self.text_value = text_value

    def draw(self):

        text(
            self.text_value,
            self.x,
            self.y
        )

# =========================================================
# STATE MACHINE
# =========================================================

STATE_BOOT = 0
STATE_IDLE = 1
STATE_MENU = 2
STATE_STATUS = 3

_current_state = STATE_BOOT

# =========================================================
# SET STATE
# =========================================================

def set_state(state):

    global _current_state

    _current_state = state

# =========================================================
# UPDATE STATE
# =========================================================

def update_state():

    if _current_state == STATE_BOOT:

        center(
            DEVICE_NAME
        )

    elif _current_state == STATE_IDLE:

        robot_eyes()

    elif _current_state == STATE_MENU:

        center("MENU")

    elif _current_state == STATE_STATUS:

        cyberpunk_dashboard(
            70,
            50,
            90
        )

    show()

# =========================================================
# ASYNC FRIENDLY
# =========================================================

async def async_loading():

    import uasyncio as asyncio

    while True:

        loading("ASYNC", 1)

        await asyncio.sleep(1)

# =========================================================
# BACKGROUND TASK
# =========================================================

def background_worker():

    while True:

        sleep_check()

        gc.collect()

        time.sleep_ms(1000)

# =========================================================
# START BACKGROUND THREAD
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
