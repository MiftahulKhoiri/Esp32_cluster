import network
import time

from config import WIFI_SSID, WIFI_PASSWORD

try:
    import led
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False


# =========================
# GET WLAN INSTANCE
# =========================

def get_wlan():

    wlan = network.WLAN(network.STA_IF)

    if not wlan.active():
        wlan.active(True)

    return wlan


# =========================
# CONNECT WIFI
# =========================

def connect_wifi(timeout=20, retry=True):

    wlan = get_wlan()

    if wlan.isconnected():

        print("WiFi already connected")

        return True

    while True:

        print("Connecting WiFi...")

        if LED_AVAILABLE:
            led.set_state("wifi_connecting")

        wlan.connect(
            WIFI_SSID,
            WIFI_PASSWORD
        )

        start = time.time()

        while not wlan.isconnected():

            time.sleep(1)

            if time.time() - start > timeout:

                print("WiFi timeout")

                break

        if wlan.isconnected():

            print("WiFi connected")

            print("IP:", wlan.ifconfig()[0])

            return True

        if not retry:

            print("WiFi failed")

            if LED_AVAILABLE:
                led.set_state("error")

            return False

        print("Retrying WiFi in 5 sec...")

        time.sleep(5)


# =========================
# CHECK WIFI CONNECTION
# =========================

def is_connected():

    wlan = get_wlan()

    return wlan.isconnected()


# =========================
# AUTO RECONNECT
# =========================

def ensure_connection():

    if not is_connected():

        print("WiFi lost")

        connect_wifi()


# =========================
# DISCONNECT
# =========================

def disconnect():

    wlan = get_wlan()

    if wlan.isconnected():

        wlan.disconnect()

        print("WiFi disconnected")