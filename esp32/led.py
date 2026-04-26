from machine import Pin, Timer   # Modul kontrol pin dan timer hardware
import micropython               # Untuk optimasi interrupt (tidak digunakan langsung di sini, tetapi umum di MicroPython)


# =========================
# CONFIG
# =========================

# Pin LED bawaan (biasanya GPIO2 pada board ESP)
LED_PIN = 2

# Konstanta status yang dapat digunakan oleh modul lain
STATE_IDLE = "idle"
STATE_WIFI = "wifi_connecting"
STATE_WIFI_CONNECTED = "wifi_connected"
STATE_OTA = "ota_updating"
STATE_MQTT = "mqtt_connected"
STATE_RUNNING = "running"
STATE_ERROR = "error"
STATE_READY = "ready"

# Durasi kedipan (dalam milidetik) untuk setiap mode tampilan LED
PERIOD_WIFI = 500        # Berkedip lambat saat mencari WiFi
PERIOD_OTA = 100         # Berkedip cepat saat OTA update
PERIOD_RUNNING = 1000    # Berkedip normal saat menjalankan tugas
PERIOD_ERROR = 2000      # Berkedip sangat lambat saat error


# =========================
# INTERNAL
# =========================

# Objek LED (Pin) — dibuat dinamis oleh init()
_led = None

# Timer untuk kedipan (Timer 1)
_timer = Timer(1)

# Status LED saat ini, disetel oleh set_state()
_state = STATE_IDLE


# =========================
# INIT
# =========================

def init(pin=LED_PIN):
    """
    Inisialisasi pin LED sebagai output dan matikan LED.
    Hanya dilakukan sekali jika _led masih None.
    Parameter 'pin' dapat disesuaikan jika menggunakan pin berbeda.
    """
    global _led
    if _led is None:
        _led = Pin(pin, Pin.OUT)   # Konfigurasi sebagai output
        _led.value(0)              # Matikan LED


# =========================
# TOGGLE
# =========================

def _toggle(timer):
    """
    Fungsi callback timer untuk membalikkan status LED (ON/OFF).
    Digunakan oleh timer untuk menghasilkan efek kedipan.
    Fungsi ini dilindungi dari exception agar tidak mengganggu interrupt.
    """
    try:
        if _led:
            _led.value(not _led.value())   # Toggle state
    except Exception:
        # Cegah crash di dalam interrupt
        pass


# =========================
# STOP
# =========================

def stop():
    """
    Menghentikan semua aktivitas LED:
    - Matikan timer kedipan
    - Matikan LED
    """
    try:
        _timer.deinit()          # Hentikan timer
    except Exception:
        pass

    if _led:
        _led.value(0)            # Matikan LED


# =========================
# SET STATE
# =========================

def set_state(new_state):
    """
    Mengubah status LED ke salah satu STATE_* yang telah ditentukan.
    Setiap status memiliki pola visual berbeda (kedip atau nyala tetap).
    Fungsi ini menghentikan timer sebelumnya (jika ada) dan menerapkan
    pola sesuai status baru. Jika status tidak berubah, fungsi langsung kembali.
    """
    global _state

    # Pastikan pin LED sudah diinisialisasi
    if _led is None:
        init()

    # Tidak melakukan apa-apa jika status yang diminta sama dengan saat ini
    if new_state == _state:
        return

    _state = new_state

    # Hentikan timer kedipan sebelumnya
    try:
        _timer.deinit()
    except Exception:
        pass

    # Terapkan pola visual berdasarkan status baru
    if new_state == STATE_IDLE:
        _led.value(0)                              # LED mati

    elif new_state == STATE_WIFI:
        _timer.init(
            period=PERIOD_WIFI,
            mode=Timer.PERIODIC,
            callback=_toggle
        )                                          # Berkedip lambat

    elif new_state == STATE_WIFI_CONNECTED:
        _led.value(1)                              # Nyala sebentar sebagai konfirmasi

    elif new_state == STATE_MQTT:
        _led.value(1)                              # Nyala stabil

    elif new_state == STATE_OTA:
        _timer.init(
            period=PERIOD_OTA,
            mode=Timer.PERIODIC,
            callback=_toggle
        )                                          # Berkedip cepat

    elif new_state == STATE_RUNNING:
        _timer.init(
            period=PERIOD_RUNNING,
            mode=Timer.PERIODIC,
            callback=_toggle
        )                                          # Berkedip normal

    elif new_state == STATE_ERROR:
        _timer.init(
            period=PERIOD_ERROR,
            mode=Timer.PERIODIC,
            callback=_toggle
        )                                          # Berkedip lambat (error)

    elif new_state == STATE_READY:
        _led.value(1)                              # Nyala stabil menandakan siap

    else:
        # Status tidak dikenal
        print("Unknown LED state:", new_state)