# Import modul hardware
from machine import Pin, Timer


# =========================
# CONFIG
# =========================

LED_PIN = 2

PERIOD_BOOT = 150
PERIOD_AP = 400
PERIOD_RUNNING = 1000
PERIOD_ERROR = 2000


# =========================
# GLOBAL
# =========================

_led = None
_timer = Timer(0)

_state = "idle"


# =========================
# INIT
# =========================

def init(pin=LED_PIN):

    global _led

    if _led is None:

        _led = Pin(
            pin,
            Pin.OUT
        )

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

    if new_state == "boot":

        _timer.init(
            period=PERIOD_BOOT,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == "ap":

        _timer.init(
            period=PERIOD_AP,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == "running":

        _timer.init(
            period=PERIOD_RUNNING,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == "error":

        _timer.init(
            period=PERIOD_ERROR,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif new_state == "activity":

        if _led:

            _led.value(1)

    else:

        if _led:

            _led.value(0)