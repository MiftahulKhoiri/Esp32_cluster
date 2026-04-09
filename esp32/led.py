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



# =========================
# INTERNAL
# =========================

_led = None

_timer = Timer(-1)

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

    _timer.deinit()

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

    _timer.deinit()

    if new_state == STATE_IDLE:

        _led.value(0)

    elif new_state == STATE_MQTT:

        _led.value(1)

    elif new_state == STATE_WIFI:

        _timer.init(
            period=500,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == STATE_OTA:

        _timer.init(
            period=100,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == STATE_RUNNING:

        _timer.init(
            period=1000,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == STATE_ERROR:

        _timer.init(
            period=2000,
            mode=Timer.PERIODIC,
            callback=_toggle
        )
    elif new_state == STATE_READY:

    _timer.init(
        period=1500,
        mode=Timer.PERIODIC,
        callback=_toggle
    )

    else:

        print("Unknown LED state:", new_state)