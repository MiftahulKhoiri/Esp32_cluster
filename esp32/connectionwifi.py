import network
import time
import machine
import gc

from config import WIFI_SSID, WIFI_PASSWORD

try:
    import led
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False


# =========================
# CONFIG
# =========================

MAX_RETRIES = 5
RETRY_DELAY = 5

MAX_FAILURE_BEFORE_RESET = 3

failure_counter = 0


# =========================
# GET WLAN
# =========================

def get_wlan():

    wlan = network.WLAN(network.STA_IF)

    if not wlan.active():

        wlan.active(True)

        time.sleep(1)

    return wlan


# =========================
# HARD RESET WIFI
# =========================

def reset_wifi():

    wlan = network.WLAN(network.STA_IF)

    try:
        wlan.disconnect()
    except:
        pass

    wlan.active(False)

    time.sleep(1)

    wlan.active(True)

    time.sleep(1)

    gc.collect()

    return wlan


# =========================
# VALIDATE IP
# =========================

def has_valid_ip(wlan):

    try:

        ip = wlan.ifconfig()[0]

        if ip == "0.0.0.0":
            return False

        if ip.startswith("169.254"):
            return False

        return True

    except:

        return False


# =========================
# CONNECT WIFI
# =========================

def connect_wifi(timeout=20, retry=True):

    global failure_counter

    retries = 0

    while True:

        wlan = reset_wifi()

        print("Connecting WiFi...")

        if LED_AVAILABLE:
            led.set_state("wifi_connecting")

        try:

            wlan.connect(
                WIFI_SSID,
                WIFI_PASSWORD
            )

        except OSError as e:

            print("Connect error:", e)

            retries += 1

            time.sleep(RETRY_DELAY)

            continue

        start = time.time()

        while True:

            if wlan.isconnected():

                if not has_valid_ip(wlan):

                    print("Connected but no IP")

                    time.sleep(1)

                    continue

                print("WiFi connected")

                print("IP:", wlan.ifconfig()[0])

                if LED_AVAILABLE:
                    led.set_state("wifi_connected")

                failure_counter = 0

                gc.collect()

                return True

            if time.time() - start > timeout:

                print("WiFi timeout")

                break

            time.sleep(1)

        status = wlan.status()

        print("WiFi status:", status)

        retries += 1

        if not retry or retries >= MAX_RETRIES:

            print("WiFi failed")

            if LED_AVAILABLE:
                led.set_state("error")

            failure_counter += 1

            print(
                "Failure count:",
                failure_counter
            )

            if failure_counter >= MAX_FAILURE_BEFORE_RESET:

                print(
                    "Too many failures — rebooting"
                )

                time.sleep(2)

                machine.reset()

            return False

        print(
            "Retrying WiFi in",
            RETRY_DELAY,
            "sec"
        )

        time.sleep(RETRY_DELAY)


# =========================
# CHECK WIFI
# =========================

def is_connected():

    wlan = network.WLAN(network.STA_IF)

    if not wlan.isconnected():
        return False

    return has_valid_ip(wlan)


# =========================
# AUTO RECONNECT
# =========================

def ensure_connection():

    wlan = network.WLAN(network.STA_IF)

    if not wlan.isconnected():

        print("WiFi lost")

        connect_wifi()

        return

    if not has_valid_ip(wlan):

        print("WiFi invalid IP")

        connect_wifi()


# =========================
# DISCONNECT
# =========================

def disconnect():

    wlan = network.WLAN(network.STA_IF)

    if wlan.isconnected():

        wlan.disconnect()

        print("WiFi disconnected")