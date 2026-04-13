from machine import Pin, Timer


# =========================
# CONFIG
# =========================

LED_PIN = 2

STATE_IDLE = "idle"
STATE_WIFI = "wifi_connecting"
STATE_OTA = "ota_updating"
STATE_MQTT = "mqtt_connected"
STATE_RUNNING = "running"
STATE_ERROR = "error"
STATE_READY = "ready"


PERIOD_WIFI = 500
PERIOD_OTA = 100
PERIOD_RUNNING = 1000
PERIOD_ERROR = 2000
PERIOD_READY = 1500


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

    _led = Pin(pin, Pin.OUT)

    _led.value(0)


# =========================
# TOGGLE
# =========================

def _toggle(timer):

    if _led:

        _led.value(not _led.value())


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

    if new_state == STATE_IDLE:

        _led.value(0)

    elif new_state == STATE_MQTT:

        _led.value(1)

    elif new_state == STATE_WIFI:

        _timer.init(
            period=PERIOD_WIFI,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

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

        _timer.init(
            period=PERIOD_READY,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    else:

        print("Unknown LED state:", new_state)