import time
import ntptime
import machine

from config import (
    INTERNET_CHECK_INTERVAL,
    NTP_SYNC_INTERVAL,
    TIMEZONE_OFFSET,
    NTP_SERVER
)

from ap_wifi import (
    connect_to_internet,
    is_internet_connected
)


# =========================
# GLOBAL TIMER
# =========================

_last_internet_check = 0
_last_ntp_sync = 0


# =========================
# SYNC TIME
# =========================

def sync_time():

    try:

        print("Syncing time from NTP")

        ntptime.host = NTP_SERVER

        ntptime.settime()

        rtc = machine.RTC()

        dt = rtc.datetime()

        hour = dt[4] + TIMEZONE_OFFSET

        if hour >= 24:
            hour -= 24

        rtc.datetime((
            dt[0],
            dt[1],
            dt[2],
            dt[3],
            hour,
            dt[5],
            dt[6],
            0
        ))

        print("Time synced")

        return True

    except Exception as e:

        print("NTP sync failed:", e)

        return False


# =========================
# INTERNET RECONNECT
# =========================

def check_internet():

    global _last_internet_check

    now = time.ticks_ms()

    if time.ticks_diff(
        now,
        _last_internet_check
    ) < INTERNET_CHECK_INTERVAL * 1000:

        return

    _last_internet_check = now

    try:

        if not is_internet_connected():

            print("Internet disconnected")

            connect_to_internet()

    except Exception as e:

        print("Internet check error:", e)


# =========================
# AUTO NTP
# =========================

def auto_ntp_sync():

    global _last_ntp_sync

    now = time.ticks_ms()

    if time.ticks_diff(
        now,
        _last_ntp_sync
    ) < NTP_SYNC_INTERVAL * 1000:

        return

    _last_ntp_sync = now

    try:

        if is_internet_connected():

            sync_time()

    except Exception as e:

        print("Auto NTP error:", e)


# =========================
# MAIN MONITOR
# =========================

def network_maintenance():

    check_internet()

    auto_ntp_sync()