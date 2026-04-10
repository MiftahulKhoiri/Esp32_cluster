import urequests
import machine
import ujson
import os
import time
import socket

from config import (
    OTA_SERVER,
    OTA_PORT,
    VERSION,
    REQUEST_TIMEOUT
)

try:
    import led
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False


TEMP_FILE = "main_new.py"
TARGET_FILE = "main.py"


# =========================
# URL
# =========================

def get_url(path):

    return "http://{}:{}/{}".format(
        OTA_SERVER,
        OTA_PORT,
        path
    )


# =========================
# CHECK UPDATE
# =========================

def check_update():

    for attempt in range(3):

        try:

            print("Checking update...")

            socket.setdefaulttimeout(
                REQUEST_TIMEOUT
            )

            url = get_url("version")

            print("URL:", url)

            response = urequests.get(url)

            data = response.json()

            response.close()

            server_version = data["version"]

            print("Current:", VERSION)
            print("Server :", server_version)

            if server_version != VERSION:

                print("Update available")

                return True

            print("No update")

            return False

        except Exception as e:

            print(
                "Update check failed:",
                e
            )

            time.sleep(2)

    return False


# =========================
# DOWNLOAD
# =========================

def download_firmware():

    for attempt in range(3):

        try:

            socket.setdefaulttimeout(
                REQUEST_TIMEOUT
            )

            if LED_AVAILABLE:

                led.set_state(
                    led.STATE_OTA
                )

            print("Downloading firmware")

            url = get_url("firmware")

            print("URL:", url)

            response = urequests.get(url)

            size = 0

            with open(
                TEMP_FILE,
                "wb"
            ) as f:

                while True:

                    chunk = response.raw.read(
                        512
                    )

                    if not chunk:

                        break

                    f.write(chunk)

                    size += len(chunk)

            response.close()

            if size == 0:

                print(
                    "Download empty"
                )

                return False

            print(
                "Downloaded:",
                size,
                "bytes"
            )

            return True

        except Exception as e:

            print(
                "Download failed:",
                e
            )

            time.sleep(2)

    return False


# =========================
# APPLY UPDATE
# =========================

def apply_update():

    try:

        if TARGET_FILE in os.listdir():

            os.remove(
                TARGET_FILE
            )

        os.rename(
            TEMP_FILE,
            TARGET_FILE
        )

        print(
            "Firmware replaced"
        )

        return True

    except Exception as e:

        print(
            "Apply update failed:",
            e
        )

        return False


# =========================
# MAIN OTA
# =========================

def perform_update():

    try:

        if not check_update():

            return False

        if not download_firmware():

            return False

        if not apply_update():

            return False

        print(
            "Restarting device"
        )

        time.sleep(2)

        machine.reset()

        return True

    except Exception as e:

        print(
            "OTA error:",
            e
        )

        return False