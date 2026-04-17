import urequests
import machine
import ujson
import os
import time
import socket

import config

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


# =========================
# HASH SUPPORT
# =========================

try:
    import hashlib
except ImportError:
    hashlib = None


TEMP_FILE = "main_new.py"
TARGET_FILE = "main.py"

EXPECTED_HASH = None


# =========================
# DNS RESOLVE
# =========================

def resolve_server():

    for _ in range(config.DNS_RESOLVE_RETRY):

        try:

            addr = socket.getaddrinfo(
                OTA_SERVER,
                OTA_PORT
            )[0][-1][0]

            print("Resolved OTA server:", addr)

            return addr

        except Exception as e:

            print("DNS resolve failed:", e)

            if config.SERVER_FALLBACK_IP:

                print("Using fallback IP")

                return config.SERVER_FALLBACK_IP

            time.sleep(config.DNS_RESOLVE_DELAY)

    raise RuntimeError("OTA server resolve failed")


# =========================
# URL
# =========================

def get_url(path):

    server_ip = resolve_server()

    return "http://{}:{}/{}".format(
        server_ip,
        OTA_PORT,
        path
    )


# =========================
# SHA256 CALCULATION
# =========================

def calculate_sha256(filepath):

    if hashlib is None:

        print("Hashlib not available")

        return None

    try:

        sha = hashlib.sha256()

        with open(filepath, "rb") as f:

            while True:

                chunk = f.read(1024)

                if not chunk:
                    break

                sha.update(chunk)

        return sha.hexdigest()

    except Exception as e:

        print("Hash calculation failed:", e)

        return None


# =========================
# CHECK UPDATE
# =========================

def check_update():

    global EXPECTED_HASH

    for attempt in range(3):

        try:

            print("Checking update...")

            url = get_url("version")

            print("URL:", url)

            response = urequests.get(
                url,
                timeout=REQUEST_TIMEOUT
            )

            data = response.json()

            response.close()

            server_version = data.get(
                "version"
            )

            server_hash = data.get(
                "sha256"
            )

            print("Current:", VERSION)
            print("Server :", server_version)

            if not server_version:

                print("Invalid version data")

                return False

            if server_version != VERSION:

                print("Update available")

                EXPECTED_HASH = server_hash

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

    global EXPECTED_HASH

    for attempt in range(3):

        try:

            if LED_AVAILABLE:

                led.set_state(
                    led.STATE_OTA
                )

            print("Downloading firmware")

            url = get_url("firmware")

            print("URL:", url)

            response = urequests.get(
                url,
                timeout=REQUEST_TIMEOUT
            )

            size = 0

            start_time = time.time()

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

                    # timeout protection

                    if time.time() - start_time > REQUEST_TIMEOUT:

                        raise RuntimeError(
                            "Download timeout"
                        )

            response.close()

            if size == 0:

                print("Download empty")

                try:
                    os.remove(TEMP_FILE)
                except:
                    pass

                return False

            print(
                "Downloaded:",
                size,
                "bytes"
            )

            # =========================
            # VERIFY HASH
            # =========================

            if EXPECTED_HASH:

                print(
                    "Verifying firmware hash"
                )

                file_hash = calculate_sha256(
                    TEMP_FILE
                )

                print(
                    "Expected:",
                    EXPECTED_HASH
                )

                print(
                    "Actual  :",
                    file_hash
                )

                if file_hash != EXPECTED_HASH:

                    print(
                        "Hash mismatch"
                    )

                    try:
                        os.remove(TEMP_FILE)
                    except:
                        pass

                    return False

                print("Hash OK")

            return True

        except Exception as e:

            print(
                "Download failed:",
                e
            )

            try:
                os.remove(TEMP_FILE)
            except:
                pass

            time.sleep(2)

    return False


# =========================
# APPLY UPDATE
# =========================

def apply_update():

    try:

        if TEMP_FILE not in os.listdir():

            print(
                "Firmware file missing"
            )

            return False

        if EXPECTED_HASH:

            print(
                "Final integrity check"
            )

            file_hash = calculate_sha256(
                TEMP_FILE
            )

            if file_hash != EXPECTED_HASH:

                print(
                    "Integrity check failed"
                )

                os.remove(
                    TEMP_FILE
                )

                return False

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

        try:
            os.remove(TEMP_FILE)
        except:
            pass

        return False


# =========================
# MAIN OTA
# =========================

def perform_update():

    attempts = 0

    MAX_ATTEMPTS = 3

    while attempts < MAX_ATTEMPTS:

        try:

            print(
                "OTA attempt:",
                attempts + 1
            )

            if not check_update():

                return False

            if not download_firmware():

                attempts += 1

                continue

            if not apply_update():

                attempts += 1

                continue

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

            attempts += 1

            time.sleep(2)

    print(
        "OTA failed after retries"
    )

    return False