# Import modul waktu dan sistem
import time
import gc

# Import konfigurasi
from config import (
    SSID,
    PASSWORD,
    DISPLAY_UPDATE_INTERVAL,
    DISPLAY_CYCLE_SECONDS,
    CLOCK_DISPLAY_DURATION,
    BOOT_DELAY
)

# Import modul sistem
from ap_wifi import (
    start_access_point,
    get_ip
)

from oled_display import (
    init_display,
    show_boot_screen,
    show_status,
    show_clock
)

from node_monitor import (
    get_node_count
)

# Import modul LED
try:
    import led_indicator as led
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False


# =========================
# GLOBAL
# =========================

_last_display_update = 0
_cycle_start_time = 0


# =========================
# DISPLAY MODE
# =========================

def is_clock_mode():
    """
    Menentukan apakah saat ini harus menampilkan jam.
    """

    now = time.ticks_ms()

    elapsed = time.ticks_diff(
        now,
        _cycle_start_time
    )

    cycle_ms = DISPLAY_CYCLE_SECONDS * 1000
    clock_ms = CLOCK_DISPLAY_DURATION * 1000

    if elapsed >= cycle_ms:
        return False

    if elapsed >= (cycle_ms - clock_ms):
        return True

    return False


# =========================
# UPDATE DISPLAY
# =========================

def update_display():
    """
    Memperbarui tampilan OLED berdasarkan mode:
    - Status
    - Clock
    """

    global _last_display_update

    now = time.ticks_ms()

    if time.ticks_diff(
        now,
        _last_display_update
    ) < DISPLAY_UPDATE_INTERVAL * 1000:
        return

    _last_display_update = now

    try:

        if is_clock_mode():

            show_clock()

        else:

            node_count = get_node_count()

            ip = get_ip()

            show_status(
                SSID,
                PASSWORD,
                ip,
                node_count
            )

            # LED activity jika ada node
            if LED_AVAILABLE:

                if node_count > 0:
                    led.set_state("activity")
                else:
                    led.set_state("running")

    except Exception as e:

        print("Display update error:", e)

        if LED_AVAILABLE:
            led.set_state("error")


# =========================
# MAIN
# =========================

def main():
    """
    Fungsi utama sistem.
    """

    global _cycle_start_time

    print("Booting Access Point Controller")

    try:

        if LED_AVAILABLE:
            led.set_state("boot")

        show_boot_screen()

        time.sleep(BOOT_DELAY)

        if LED_AVAILABLE:
            led.set_state("ap")

        start_access_point()

        init_display()

        gc.collect()

        _cycle_start_time = time.ticks_ms()

        if LED_AVAILABLE:
            led.set_state("running")

        print("System ready")

    except Exception as e:

        print("Boot error:", e)

        if LED_AVAILABLE:
            led.set_state("error")

    while True:

        try:

            now = time.ticks_ms()

            cycle_ms = DISPLAY_CYCLE_SECONDS * 1000

            if time.ticks_diff(
                now,
                _cycle_start_time
            ) >= cycle_ms:

                _cycle_start_time = now

            update_display()

        except Exception as e:

            print("Main loop error:", e)

            if LED_AVAILABLE:
                led.set_state("error")

        time.sleep(0.1)


# =========================
# START
# =========================

main()