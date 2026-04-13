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


MAX_RETRIES = 5
RETRY_DELAY = 5


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


def connect_wifi(timeout=20, retry=True):

    retries = 0

    while True:

        wlan = reset_wifi()

        print("Connecting WiFi...")

        if LED_AVAILABLE:
            led.set_state(led.STATE_WIFI)

        try:

            wlan.connect(
                WIFI_SSID,
                WIFI_PASSWORD
            )

        except OSError as e:

            print("Connect error:", e)

            retries += 1

            if retries >= MAX_RETRIES:

                if LED_AVAILABLE:
                    led.set_state(led.STATE_ERROR)

                return False

            time.sleep(RETRY_DELAY)

            continue

        start = time.time()

        while True:

            if wlan.isconnected():

                print("WiFi connected")

                print("IP:", wlan.ifconfig()[0])

                if LED_AVAILABLE:
                    led.set_state(led.STATE_WIFI_CONNECTED)

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
                led.set_state(led.STATE_ERROR)

            return False

        print("Retrying WiFi in", RETRY_DELAY, "sec")

        time.sleep(RETRY_DELAY)