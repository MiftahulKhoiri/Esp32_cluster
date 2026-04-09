import urequests
import machine
import ujson
import os

from config import OTA_SERVER, OTA_PORT, VERSION


def get_url(path):

    return "http://{}:{}/{}".format(
        OTA_SERVER,
        OTA_PORT,
        path
    )


def check_update():

    try:

        url = get_url("version")

        response = urequests.get(url)

        data = response.json()

        server_version = data["version"]

        response.close()

        print("Current:", VERSION)
        print("Server :", server_version)

        if server_version != VERSION:

            print("Update available")

            return True

        print("No update")

        return False

    except Exception as e:

        print("Update check failed:", e)

        return False


def download_firmware():

    try:

        print("Downloading firmware")

        url = get_url("firmware")

        response = urequests.get(url)

        with open("main.py", "wb") as f:

            f.write(response.content)

        response.close()

        print("Firmware updated")

        return True

    except Exception as e:

        print("Download failed:", e)

        return False


def perform_update():

    if check_update():

        if download_firmware():

            print("Restarting")

            machine.reset()