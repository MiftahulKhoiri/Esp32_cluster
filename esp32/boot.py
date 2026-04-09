import network
import time
from config import WIFI_SSID, WIFI_PASSWORD

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        timeout = 0
        while not wlan.isconnected():
            time.sleep(1)
            timeout += 1

            if timeout > 20:
                print("WiFi failed")
                return

    print("WiFi connected")
    print(wlan.ifconfig())

connect_wifi()