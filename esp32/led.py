from machine import Pin, Timer

LED_PIN = 2  # default ESP32 onboard LED

led = Pin(LED_PIN, Pin.OUT)

timer = Timer(0)

state = "idle"


def _toggle(timer):

    led.value(not led.value())


def set_state(new_state):

    global state

    state = new_state

    timer.deinit()

    if state == "idle":

        led.value(0)

    elif state == "mqtt_connected":

        led.value(1)

    elif state == "wifi_connecting":

        timer.init(
            period=500,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif state == "ota_updating":

        timer.init(
            period=100,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif state == "running":

        timer.init(
            period=1000,
            mode=Timer.PERIODIC,
            callback=_toggle
        )

    elif state == "error":

        timer.init(
            period=2000,
            mode=Timer.PERIODIC,
            callback=_toggle
        )