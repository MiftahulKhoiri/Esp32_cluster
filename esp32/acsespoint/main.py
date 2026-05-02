# =========================
# IMPORT
# =========================

import time
import gc

from config import (
    SSID,
    PASSWORD,

    STATUS_DISPLAY_DURATION,
    CLOCK_DISPLAY_DURATION,

    CLOCK_REFRESH_INTERVAL,
    NODE_REFRESH_INTERVAL,
    DISPLAY_LOOP_DELAY,

    BOOT_DELAY
)

from ap_wifi import (
    start_access_point,
    get_ip
)

from oled_display import (
    init_display,
    show_logo_animation,
    show_boot_screen,
    show_status,
    show_clock
)

from node_monitor import (
    get_node_count
)

try:
    import led_indicator as led
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False


# =========================
# GLOBAL STATE
# =========================

_current_screen = "status"

_screen_start_time = 0
_last_clock_update = 0
_last_node_update = 0

_cached_node_count = 0


# =========================
# SCREEN SWITCH LOGIC
# =========================

def switch_screen():

    global _current_screen
    global _screen_start_time

    now = time.ticks_ms()

    elapsed = time.ticks_diff(
        now,
        _screen_start_time
    )

    if _current_screen == "status":

        if elapsed >= STATUS_DISPLAY_DURATION * 1000:

            _current_screen = "clock"

            _screen_start_time = now

    elif _current_screen == "clock":

        if elapsed >= CLOCK_DISPLAY_DURATION * 1000:

            _current_screen = "status"

            _screen_start_time = now


# =========================
# UPDATE DISPLAY
# =========================

def update_display():

    global _last_clock_update
    global _last_node_update
    global _cached_node_count

    now = time.ticks_ms()

    switch_screen()

    try:

        # =====================
        # STATUS SCREEN
        # =====================

        if _current_screen == "status":

            # update node periodik

            if time.ticks_diff(
                now,
                _last_node_update
            ) >= NODE_REFRESH_INTERVAL * 1000:

                _cached_node_count = get_node_count()

                _last_node_update = now

            ip = get_ip()

            show_status(
                SSID,
                PASSWORD,
                ip,
                _cached_node_count
            )

            if LED_AVAILABLE:

                if _cached_node_count > 0:
                    led.set_state("activity")
                else:
                    led.set_state("running")

        # =====================
        # CLOCK SCREEN
        # =====================

        elif _current_screen == "clock":

            if time.ticks_diff(
                now,
                _last_clock_update
            ) >= CLOCK_REFRESH_INTERVAL * 1000:

                show_clock()

                _last_clock_update = now

    except Exception as e:

        print("Display update error:", e)

        if LED_AVAILABLE:
            led.set_state("error")


# =========================
# MAIN
# =========================

def main():

    global _screen_start_time

    print("Booting Access Point Controller")

    try:

        if LED_AVAILABLE:
            led.set_state("boot")

        # INIT DISPLAY

        init_display()

        # LOGO

        show_logo_animation()

        # BOOT SCREEN

        show_boot_screen()

        time.sleep(BOOT_DELAY)

        if LED_AVAILABLE:
            led.set_state("ap")

        # START AP

        start_access_point()

        gc.collect()

        # INIT TIMER

        _screen_start_time = time.ticks_ms()

        if LED_AVAILABLE:
            led.set_state("running")

        print("System ready")

    except Exception as e:

        print("Boot error:", e)

        if LED_AVAILABLE:
            led.set_state("error")

    # =========================
    # MAIN LOOP
    # =========================

    while True:

        try:

            update_display()

        except Exception as e:

            print("Main loop error:", e)

            if LED_AVAILABLE:
                led.set_state("error")

        time.sleep(DISPLAY_LOOP_DELAY)


# =========================
# START
# =========================

main()