# =========================================================
# MAIN APPLICATION
# File: main.py
# =========================================================
#
# Production Ready
# ESP32 + MicroPython
# Access Point Controller
#
# Fitur:
# - Hardware watchdog
# - OLED screen manager
# - Network maintenance
# - RTC sync
# - Memory protection
# - Runtime recovery
# - LED status
# - Screen rotation
# - Long runtime stability
#
# =========================================================


# =========================================================
# IMPORT
# =========================================================

import time
import gc

from machine import WDT

from config import (

    SSID,
    PASSWORD,

    STATUS_INFO_DURATION,
    STATUS_HEALTH_DURATION,
    CLOCK_DISPLAY_DURATION,

    CLOCK_REFRESH_INTERVAL,
    NODE_REFRESH_INTERVAL,

    DISPLAY_LOOP_DELAY,

    WATCHDOG_TIMEOUT,
    BOOT_DELAY
)

from ap_wifi import (
    start_gateway,
    get_ip
)

from oled_display import (

    init,

    show_logo_animation,
    show_boot_screen,

    show_status_info,
    show_status_health,
    show_clock,

    sleep_check
)

from network_monitor import (
    network_maintenance,
    sync_time
)

from node_monitor import (
    get_node_count
)


# =========================================================
# OPTIONAL LED MODULE
# =========================================================

try:

    import led_indicator as led

    LED_AVAILABLE = True

except Exception as e:

    print("LED module unavailable:", e)

    LED_AVAILABLE = False


# =========================================================
# WATCHDOG
# =========================================================

wdt = WDT(
    timeout=WATCHDOG_TIMEOUT
)


# =========================================================
# GLOBAL STATE
# =========================================================

_current_screen = "status_info"

_screen_start_time = 0

_last_clock_update = 0

_last_node_update = 0

_last_gc = 0

_cached_node_count = 0


# =========================================================
# SAFE LED CONTROL
# =========================================================

def set_led(state):

    if not LED_AVAILABLE:
        return

    try:

        led.set_state(state)

    except Exception as e:

        print("LED error:", e)


# =========================================================
# SCREEN SWITCHER
# =========================================================

def switch_screen():

    global _current_screen
    global _screen_start_time

    now = time.ticks_ms()

    elapsed = time.ticks_diff(
        now,
        _screen_start_time
    )

    # =====================================
    # STATUS INFO -> STATUS HEALTH
    # =====================================

    if _current_screen == "status_info":

        if elapsed >= (
            STATUS_INFO_DURATION * 1000
        ):

            _current_screen = "status_health"

            _screen_start_time = now

    # =====================================
    # STATUS HEALTH -> CLOCK
    # =====================================

    elif _current_screen == "status_health":

        if elapsed >= (
            STATUS_HEALTH_DURATION * 1000
        ):

            _current_screen = "clock"

            _screen_start_time = now

    # =====================================
    # CLOCK -> STATUS INFO
    # =====================================

    elif _current_screen == "clock":

        if elapsed >= (
            CLOCK_DISPLAY_DURATION * 1000
        ):

            _current_screen = "status_info"

            _screen_start_time = now


# =========================================================
# UPDATE DISPLAY
# =========================================================

def update_display():

    global _last_clock_update
    global _last_node_update
    global _cached_node_count

    now = time.ticks_ms()

    # Update screen state
    switch_screen()

    try:

        # =================================
        # STATUS INFO
        # =================================

        if _current_screen == "status_info":

            ip = get_ip()

            show_status_info(
                SSID,
                PASSWORD,
                ip
            )

        # =================================
        # STATUS HEALTH
        # =================================

        elif _current_screen == "status_health":

            # Refresh node count
            if time.ticks_diff(
                now,
                _last_node_update
            ) >= (
                NODE_REFRESH_INTERVAL * 1000
            ):

                try:

                    _cached_node_count = (
                        get_node_count()
                    )

                except Exception as e:

                    print(
                        "Node count error:",
                        e
                    )

                    _cached_node_count = 0

                _last_node_update = now

            # Render OLED
            show_status_health(
                _cached_node_count
            )

            # LED indicator
            if _cached_node_count > 0:

                set_led("activity")

            else:

                set_led("running")

        # =================================
        # CLOCK
        # =================================

        elif _current_screen == "clock":

            # Clock selalu update
            if time.ticks_diff(
                now,
                _last_clock_update
            ) >= (
                CLOCK_REFRESH_INTERVAL * 1000
            ):

                show_clock()

                _last_clock_update = now

    except Exception as e:

        print(
            "Display update error:",
            e
        )

        set_led("error")


# =========================================================
# PERIODIC MEMORY CLEANER
# =========================================================

def memory_maintenance():

    global _last_gc

    now = time.ticks_ms()

    # GC setiap 30 detik
    if time.ticks_diff(
        now,
        _last_gc
    ) >= 30000:

        gc.collect()

        _last_gc = now


# =========================================================
# BOOT SEQUENCE
# =========================================================

def boot_sequence():

    global _screen_start_time

    print(
        "Booting Access Point Controller"
    )

    set_led("boot")

    # =====================================
    # WATCHDOG
    # =====================================

    wdt.feed()

    # =====================================
    # OLED INIT
    # =====================================

    if not init():

        print("OLED initialization failed")

    wdt.feed()

    # =====================================
    # LOGO ANIMATION
    # =====================================

    try:

        show_logo_animation()

    except Exception as e:

        print(
            "Logo animation error:",
            e
        )

    wdt.feed()

    # =====================================
    # BOOT SCREEN
    # =====================================

    try:

        show_boot_screen()

    except Exception as e:

        print(
            "Boot screen error:",
            e
        )

    time.sleep(BOOT_DELAY)

    set_led("ap")

    # =====================================
    # START NETWORK
    # =====================================

    print("Starting gateway")

    gateway_ok = False

    try:

        gateway_ok = start_gateway()

    except Exception as e:

        print(
            "Gateway start error:",
            e
        )

    if gateway_ok:

        print("Gateway started")

    else:

        print("Gateway failed")

        set_led("error")

    wdt.feed()

    # =====================================
    # INITIAL TIME SYNC
    # =====================================

    try:

        sync_time()

        print("NTP sync success")

    except Exception as e:

        print(
            "Initial NTP sync failed:",
            e
        )

    # =====================================
    # MEMORY CLEANUP
    # =====================================

    gc.collect()

    # =====================================
    # INIT TIMER
    # =====================================

    _screen_start_time = (
        time.ticks_ms()
    )

    set_led("running")

    print("System ready")


# =========================================================
# MAIN LOOP
# =========================================================

def run():

    while True:

        try:

            # =============================
            # UPDATE OLED
            # =============================

            update_display()

            # =============================
            # NETWORK MAINTENANCE
            # =============================

            network_maintenance()

            # =============================
            # OLED AUTO SLEEP
            # =============================

            sleep_check()

            # =============================
            # MEMORY MAINTENANCE
            # =============================

            memory_maintenance()

            # =============================
            # WATCHDOG FEED
            # =============================

            wdt.feed()

        except Exception as e:

            print(
                "Main loop error:",
                e
            )

            set_led("error")

            gc.collect()

        # =============================
        # LOOP DELAY
        # =============================

        time.sleep(
            DISPLAY_LOOP_DELAY
        )


# =========================================================
# MAIN ENTRY
# =========================================================

def main():

    try:

        boot_sequence()

        run()

    except Exception as e:

        print(
            "Fatal system error:",
            e
        )

        set_led("error")

        while True:

            try:

                wdt.feed()

            except:
                pass

            time.sleep(1)


# =========================================================
# START SYSTEM
# =========================================================

main()