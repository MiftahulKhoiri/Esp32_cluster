# Import library untuk HTTP request (urequests), kontrol hardware, JSON, file system, waktu, dan socket
import urequests
import machine
import ujson
import os
import time
import socket

# Ambil konfigurasi dari file config
import config
from config import (
    OTA_SERVER,
    OTA_PORT,
    VERSION,
    REQUEST_TIMEOUT
)

# Coba impor modul LED; jika gagal, set LED_AVAILABLE = False
try:
    import led
    LED_AVAILABLE = True
except Exception:
    LED_AVAILABLE = False


# =========================
# HASH SUPPORT
# =========================

# Coba impor hashlib untuk verifikasi SHA256, jika tidak ada biarkan None
try:
    import hashlib
except ImportError:
    hashlib = None


# Nama file sementara untuk firmware yang diunduh
TEMP_FILE = "main_new.py"
# Nama file target yang akan dijalankan (firmware utama)
TARGET_FILE = "main.py"

# Variabel global untuk menyimpan hash yang diharapkan dari server
EXPECTED_HASH = None


# =========================
# DNS RESOLVE
# =========================

def resolve_server():
    """
    Melakukan resolusi DNS untuk mendapatkan alamat IP server OTA.
    Jika gagal sebanyak DNS_RESOLVE_RETRY kali, akan menggunakan IP fallback
    (jika tersedia) atau melemparkan RuntimeError.
    """
    for _ in range(config.DNS_RESOLVE_RETRY):
        try:
            # Dapatkan alamat IP dari host server OTA
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
    """
    Membentuk URL lengkap ke server OTA berdasarkan alamat IP hasil resolusi,
    port, dan path yang diberikan.
    """
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
    """
    Menghitung hash SHA256 dari sebuah file secara bertahap (mendukung file besar).
    Mengembalikan string hex digest atau None jika hashlib tidak tersedia/gagal.
    """
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
    """
    Memeriksa ketersediaan pembaruan firmware dengan membandingkan versi lokal
    dan versi server.
    """
    global EXPECTED_HASH

    for attempt in range(3):
        try:
            print("Checking update...")
            url = get_url("version")
            print("URL:", url)

            response = urequests.get(url, timeout=REQUEST_TIMEOUT)
            data = response.json()
            response.close()

            server_version = data.get("version")
            server_hash = data.get("sha256")

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
            print("Update check failed:", e)
            time.sleep(2)

    return False


# =========================
# DOWNLOAD
# =========================

def download_firmware():
    """
    Mengunduh firmware dari server OTA dan menyimpannya ke file sementara.
    """
    global EXPECTED_HASH

    for attempt in range(3):
        try:
            if LED_AVAILABLE:
                led.set_state(led.STATE_OTA)

            print("Downloading firmware")
            url = get_url("firmware")
            print("URL:", url)

            response = urequests.get(url, timeout=REQUEST_TIMEOUT)

            size = 0
            start_time = time.ticks_ms()

            with open(TEMP_FILE, "wb") as f:
                while True:
                    chunk = response.raw.read(512)
                    if not chunk:
                        break

                    f.write(chunk)
                    size += len(chunk)

                    if time.ticks_diff(
                        time.ticks_ms(),
                        start_time
                    ) > REQUEST_TIMEOUT * 1000:
                        raise RuntimeError("Download timeout")

            response.close()

            if size == 0:
                print("Download empty")
                try:
                    os.remove(TEMP_FILE)
                except Exception:
                    pass
                return False

            print("Downloaded:", size, "bytes")

            if EXPECTED_HASH:
                print("Verifying firmware hash")

                file_hash = calculate_sha256(TEMP_FILE)

                print("Expected:", EXPECTED_HASH)
                print("Actual  :", file_hash)

                if file_hash != EXPECTED_HASH:
                    print("Hash mismatch")

                    try:
                        os.remove(TEMP_FILE)
                    except Exception:
                        pass

                    return False

                print("Hash OK")

            return True

        except Exception as e:
            print("Download failed:", e)

            try:
                os.remove(TEMP_FILE)
            except Exception:
                pass

            time.sleep(2)

    return False


# =========================
# APPLY UPDATE
# =========================

def apply_update():
    """
    Menerapkan firmware yang sudah diunduh.
    """
    try:
        if TEMP_FILE not in os.listdir():
            print("Firmware file missing")
            return False

        if EXPECTED_HASH:
            print("Final integrity check")

            file_hash = calculate_sha256(TEMP_FILE)

            if file_hash != EXPECTED_HASH:
                print("Integrity check failed")

                os.remove(TEMP_FILE)

                return False

        if TARGET_FILE in os.listdir():
            os.remove(TARGET_FILE)

        os.rename(TEMP_FILE, TARGET_FILE)

        print("Firmware replaced")

        return True

    except Exception as e:
        print("Apply update failed:", e)

        try:
            os.remove(TEMP_FILE)
        except Exception:
            pass

        return False


# =========================
# MAIN OTA
# =========================

def perform_update():
    """
    Fungsi utama untuk melakukan seluruh proses OTA update.
    """
    attempts = 0
    MAX_ATTEMPTS = 3

    while attempts < MAX_ATTEMPTS:
        try:
            print("OTA attempt:", attempts + 1)

            if not check_update():
                return False

            if not download_firmware():
                attempts += 1
                continue

            if not apply_update():
                attempts += 1
                continue

            print("Restarting device")

            time.sleep(2)

            machine.reset()

            return True

        except Exception as e:
            print("OTA error:", e)

            attempts += 1

            time.sleep(2)

    print("OTA failed after retries")

    return False