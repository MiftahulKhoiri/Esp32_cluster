# Import modul network dan waktu
import network
import time

# Ambil konfigurasi dari file config
from config import (
    SSID,
    PASSWORD,
    CHANNEL,
    MAX_CLIENTS,
    AP_IP,
    SUBNET,
    GATEWAY,

    INTERNET_SSID,
    INTERNET_PASSWORD,
    INTERNET_CONNECT_TIMEOUT
)

# =========================
# GLOBAL
# =========================

_ap = None
_sta = None


# =========================
# CONNECT INTERNET (STA)
# =========================

def connect_to_internet():

    global _sta

    try:

        print("Connecting to Internet")

        _sta = network.WLAN(network.STA_IF)

        _sta.active(True)

        if _sta.isconnected():

            print("Internet already connected")

            print("STA IP:", _sta.ifconfig()[0])

            return True

        _sta.connect(
            INTERNET_SSID,
            INTERNET_PASSWORD
        )

        timeout = INTERNET_CONNECT_TIMEOUT

        while not _sta.isconnected():

            time.sleep(1)

            timeout -= 1

            print("Waiting internet...", timeout)

            if timeout <= 0:

                print("Internet connection timeout")

                return False

        print("Internet connected")

        print("STA IP:", _sta.ifconfig()[0])

        return True

    except Exception as e:

        print("Internet connect error:", e)

        return False


# =========================
# ENABLE NAT
# =========================

def enable_nat():

    try:

        print("Enabling NAT")

        if hasattr(network, "NAT"):

            network.NAT.enable()

            print("NAT enabled")

            return True

        else:

            print("NAT feature not available")

            return False

    except Exception as e:

        print("NAT error:", e)

        return False


# =========================
# START ACCESS POINT
# =========================

def start_access_point():

    global _ap

    try:

        _ap = network.WLAN(network.AP_IF)

        if not _ap.active():

            _ap.active(True)

            time.sleep(1)

        print("Starting Access Point")

        _ap.config(
            essid=SSID,
            password=PASSWORD,
            channel=CHANNEL,
            max_clients=MAX_CLIENTS,
            authmode=network.AUTH_WPA_WPA2_PSK
        )

        _ap.ifconfig((
            AP_IP,
            SUBNET,
            GATEWAY,
            GATEWAY
        ))

        time.sleep(1)

        print("Access Point started")

        print("SSID :", SSID)

        print("AP IP:", _ap.ifconfig()[0])

        return True

    except Exception as e:

        print("AP start error:", e)

        return False


# =========================
# START GATEWAY
# =========================

def start_gateway():

    print("Starting Gateway")

    internet_ok = connect_to_internet()

    ap_ok = start_access_point()

    nat_ok = enable_nat()

    print("Gateway status")

    print("Internet:", internet_ok)

    print("Access Point:", ap_ok)

    print("NAT:", nat_ok)

    if ap_ok:

        print("Gateway ready")

        return True

    else:

        print("Gateway failed")

        return False


# =========================
# GET AP
# =========================

def get_ap():

    global _ap

    if _ap is None:

        _ap = network.WLAN(network.AP_IF)

    return _ap


# =========================
# GET IP ADDRESS
# =========================

def get_ip():

    try:

        ap = get_ap()

        return ap.ifconfig()[0]

    except Exception:

        return "0.0.0.0"


# =========================
# GET INTERNET IP
# =========================

def get_internet_ip():

    try:

        if _sta and _sta.isconnected():

            return _sta.ifconfig()[0]

    except Exception:

        pass

    return "0.0.0.0"


# =========================
# INTERNET STATUS
# =========================

def is_internet_connected():

    try:

        if _sta:

            return _sta.isconnected()

    except Exception:

        pass

    return False


# =========================
# GET CONNECTED STATIONS
# =========================

def get_connected_clients():

    try:

        ap = get_ap()

        stations = ap.status("stations")

        return stations

    except Exception as e:

        print("Station list error:", e)

        return []


# =========================
# GET CLIENT COUNT
# =========================

def get_client_count():

    try:

        return len(get_connected_clients())

    except Exception:

        return 0


# =========================
# IS ACTIVE
# =========================

def is_active():

    try:

        ap = get_ap()

        return ap.active()

    except Exception:

        return False