# Import library untuk koneksi WiFi (network), waktu, kontrol hardware, dan garbage collector
import network
import time
import machine
import gc

# Ambil konfigurasi SSID dan password WiFi dari file config
from config import WIFI_SSID, WIFI_PASSWORD

# Coba impor modul LED, jika gagal set LED_AVAILABLE = False
try:
    import led
    LED_AVAILABLE = True
except Exception:
    LED_AVAILABLE = False


# =========================
# CONFIG
# =========================

# Jumlah maksimal percobaan koneksi ulang sebelum menyerah (per sesi connect_wifi)
MAX_RETRIES = 5
# Jeda waktu antar percobaan ulang (detik)
RETRY_DELAY = 5

# Batas kegagalan berturut-turut sebelum node melakukan reboot
MAX_FAILURE_BEFORE_RESET = 3

# Penghitung kegagalan berturut-turut (bersifat global untuk siklus hidup node)
failure_counter = 0


# =========================
# GET WLAN
# =========================

def get_wlan():
    """
    Mengembalikan objek WLAN mode station (STA).
    Jika interface belum aktif, aktifkan terlebih dahulu.
    """
    wlan = network.WLAN(network.STA_IF)   # Buat objek station

    if not wlan.active():
        wlan.active(True)                 # Aktifkan interface WiFi
        time.sleep(1)                     # Tunggu sebentar

    return wlan


# =========================
# HARD RESET WIFI
# =========================

def reset_wifi():
    """
    Melakukan reset perangkat keras pada modul WiFi:
    - Putuskan koneksi jika ada.
    - Nonaktifkan interface, lalu aktifkan kembali.
    - Lakukan pembersihan memori.
    Mengembalikan objek WLAN yang baru direset.
    """
    wlan = network.WLAN(network.STA_IF)   # Dapatkan interface STA

    try:
        wlan.disconnect()                 # Putuskan koneksi bila ada
    except Exception:
        pass

    wlan.active(False)                    # Matikan interface
    time.sleep(1)
    wlan.active(True)                     # Hidupkan kembali
    time.sleep(1)

    gc.collect()                          # Bersihkan memori

    return wlan


# =========================
# VALIDATE IP
# =========================

def has_valid_ip(wlan):
    """
    Memeriksa apakah interface WLAN memiliki alamat IP yang valid (bukan 0.0.0.0
    atau alamat APIPA 169.254.x.x). Mengembalikan True jika valid.
    """
    try:
        ip = wlan.ifconfig()[0]           # Dapatkan alamat IP

        if ip == "0.0.0.0":              # IP nol tidak valid
            return False

        if ip.startswith("169.254"):     # IP APIPA (self-assigned) tidak valid
            return False

        return True
    except Exception:
        return False


# =========================
# CONNECT WIFI
# =========================

def connect_wifi(timeout=20, retry=True):
    """
    Menghubungkan node ke WiFi dengan parameter:
    - timeout: batas waktu per percobaan koneksi (detik).
    - retry: jika True, akan mencoba ulang hingga MAX_RETRIES kali jika gagal.
    Menangani kegagalan berulang: jika jumlah kegagalan berturut-turut mencapai
    MAX_FAILURE_BEFORE_RESET, node akan di-reboot.
    Mengembalikan True jika berhasil, False jika gagal.
    """
    global failure_counter

    retries = 0

    while True:
        wlan = reset_wifi()               # Reset interface WiFi di setiap percobaan

        print("Connecting WiFi...")

        if LED_AVAILABLE:
            led.set_state("wifi_connecting")

        try:
            # Coba sambungkan ke AP dengan SSID dan password
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        except OSError as e:
            print("Connect error:", e)
            retries += 1
            time.sleep(RETRY_DELAY)
            continue

        start = time.ticks_ms()

        # Tunggu hingga terhubung atau timeout
        while True:
            if wlan.isconnected():
                # Sudah terkoneksi, tapi cek apakah IP valid
                if not has_valid_ip(wlan):
                    print("Connected but no IP")
                    time.sleep(1)
                    continue

                print("WiFi connected")
                print("IP:", wlan.ifconfig()[0])

                if LED_AVAILABLE:
                    led.set_state("wifi_connected")

                failure_counter = 0       # Reset penghitung kegagalan
                gc.collect()              # Bersihkan memori setelah berhasil
                return True

            if time.ticks_diff(time.ticks_ms(), start) > timeout * 1000:
                print("WiFi timeout")
                break

            time.sleep(1)

        status = wlan.status()            # Status kode error WiFi
        print("WiFi status:", status)

        retries += 1

        if not retry or retries >= MAX_RETRIES:
            print("WiFi failed")

            if LED_AVAILABLE:
                led.set_state("error")

            failure_counter += 1
            print("Failure count:", failure_counter)

            if failure_counter >= MAX_FAILURE_BEFORE_RESET:
                print("Too many failures — rebooting")
                time.sleep(2)
                machine.reset()           # Reboot node

            return False

        print("Retrying WiFi in", RETRY_DELAY, "sec")
        time.sleep(RETRY_DELAY)


# =========================
# CHECK WIFI
# =========================

def is_connected():
    """
    Memeriksa status koneksi WiFi saat ini.
    Mengembalikan True jika terhubung dan memiliki IP valid.
    """
    wlan = network.WLAN(network.STA_IF)   # Dapatkan interface STA

    if not wlan.isconnected():            # Jika tidak terhubung, langsung False
        return False

    return has_valid_ip(wlan)             # Periksa validitas IP


# =========================
# AUTO RECONNECT
# =========================

def ensure_connection():
    """
    Memastikan koneksi WiFi tetap terjaga.
    Dipanggil secara berkala di loop utama. Jika terdeteksi putus atau
    IP tidak valid, akan memanggil connect_wifi untuk menyambung ulang.
    """
    wlan = network.WLAN(network.STA_IF)

    if not wlan.isconnected():            # WiFi terputus
        print("WiFi lost")
        connect_wifi()
        return

    if not has_valid_ip(wlan):            # IP tidak valid (mungkin 169.254.x.x)
        print("WiFi invalid IP")
        connect_wifi()


# =========================
# DISCONNECT
# =========================

def disconnect():
    """
    Memutuskan koneksi WiFi secara sengaja.
    """
    wlan = network.WLAN(network.STA_IF)

    if wlan.isconnected():
        wlan.disconnect()
        print("WiFi disconnected")