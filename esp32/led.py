from machine import Pin, Timer
import micropython


# =========================
# CONFIG
# =========================

LED_PIN = 2

STATE_IDLE = "idle"
STATE_WIFI = "wifi_connecting"
STATE_WIFI_CONNECTED = "wifi_connected"
STATE_OTA = "ota_updating"
STATE_MQTT = "mqtt_connected"
STATE_RUNNING = "running"
STATE_ERROR = "error"
STATE_READY = "ready"


PERIOD_WIFI = 500
PERIOD_OTA = 100
PERIOD_RUNNING = 1000
PERIOD_ERROR = 2000


# =========================
# INTERNAL
# =========================

_led = None

_timer = Timer(1)

_state = STATE_IDLE


# =========================
# INIT
# =========================

def init(pin=LED_PIN):

    global _led

    if _led is None:

        _led = Pin(pin, Pin.OUT)

        _led.value(0)


# =========================
# TOGGLE
# =========================

def _toggle(timer):

    try:

        if _led:

            _led.value(
                not _led.value()
            )

    except Exception:

        # prevent crash inside interrupt
        pass


# =========================
# STOP
# =========================

def stop():

    try:
        _timer.deinit()
    except:
        pass

    if _led:

        _led.value(0)


# =========================
# SET STATE
# =========================

def set_state(new_state):

    global _state

    if _led is None:

        init()

    if new_state == _state:

        return

    _state = new_state

    try:
        _timer.deinit()
    except:
        pass

    # ---------------------

    if new_state == STATE_IDLE:

        _led.value(0)

    elif new_state == STATE_WIFI:

        _timer.init(
            period=PERIOD_WIFI,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == STATE_WIFI_CONNECTED:

        # short confirmation blink
        _led.value(1)

    elif new_state == STATE_MQTT:

        # steady ON
        _led.value(1)

    elif new_state == STATE_OTA:

        _timer.init(
            period=PERIOD_OTA,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == STATE_RUNNING:

        _timer.init(
            period=PERIOD_RUNNING,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == STATE_ERROR:

        _timer.init(
            period=PERIOD_ERROR,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == STATE_READY:

        # steady ON
        _led.value(1)

    else:

        print("Unknown LED state:", new_state)