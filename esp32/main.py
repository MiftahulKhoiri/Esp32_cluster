import network
import time
from machine import Pin
from umqtt.simple import MQTTClient
import ujson
import machine

# =============================
# CONFIGURATION
# =============================

SSID = "Ap"
PASSWORD = "1234567891"

BROKER = "192.168.250.4"

CLIENT_ID = "node1"

LED_PIN = 2

HEARTBEAT_INTERVAL = 5000

# =============================
# HARDWARE
# =============================

LED = Pin(LED_PIN, Pin.OUT)

def led_on():
    LED.value(1)

def led_off():
    LED.value(0)

def blink(times=1, delay=0.2):

    for _ in range(times):

        LED.value(1)
        time.sleep(delay)

        LED.value(0)
        time.sleep(delay)

def heartbeat_led():

    LED.value(1)
    time.sleep(0.05)

    LED.value(0)

# =============================
# WIFI
# =============================

def connect_wifi():

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    print("Connecting WiFi...")

    wlan.connect(SSID, PASSWORD)

    timeout = 20

    while not wlan.isconnected():

        print("Status:", wlan.status())

        LED.value(1)
        time.sleep(0.3)

        LED.value(0)
        time.sleep(0.3)

        timeout -= 1

        if timeout <= 0:

            print("WiFi FAILED")

            return False

    print("Connected:", wlan.ifconfig())

    led_on()

    return True

# =============================
# MACHINE LEARNING
# =============================

def train_linear(data):

    x = data["x"]
    y = data["y"]

    a = data["a"]
    b = data["b"]

    # prediction

    y_pred = a * x + b

    error = y_pred - y

    grad_a = error * x
    grad_b = error

    return {

        "grad_a": grad_a,
        "grad_b": grad_b

    }

# =============================
# COMMAND EXECUTION
# =============================

def execute_command(cmd, value):

    if cmd == "square":

        return value * value

    if cmd == "double":

        return value * 2

    if cmd == "train":

        return train_linear(value)

    if cmd == "led_on":

        led_on()
        return "LED ON"

    if cmd == "led_off":

        led_off()
        return "LED OFF"

    return "unknown command"

# =============================
# TASK PROCESSING
# =============================

def process_task(data):

    task_id = data["task_id"]

    command = data["command"]

    value = data.get("value", {})

    result = execute_command(command, value)

    response = {

        "node": CLIENT_ID,
        "task_id": task_id,
        "result": result,
        "status": "done"

    }

    return response

# =============================
# MQTT CALLBACK
# =============================

def on_message(topic, msg):

    print("Task received:", msg)

    blink(1)

    data = ujson.loads(msg)

    response = process_task(data)

    client.publish(
        "node/result",
        ujson.dumps(response)
    )

# =============================
# HEARTBEAT
# =============================

def send_status():

    status = {

        "node": CLIENT_ID,
        "status": "alive",
        "uptime_ms": time.ticks_ms()

    }

    client.publish(
        "node/status",
        ujson.dumps(status)
    )

    heartbeat_led()

# =============================
# MAIN
# =============================

if not connect_wifi():

    print("Restarting...")

    time.sleep(5)

    machine.reset()

print("Connecting MQTT...")

client = MQTTClient(
    CLIENT_ID,
    BROKER
)

client.set_callback(on_message)

client.connect()

print("MQTT connected")

blink(2)

client.subscribe("node/task")

print("Waiting task...")

last_heartbeat = time.ticks_ms()

while True:

    try:

        client.check_msg()

        now = time.ticks_ms()

        if time.ticks_diff(
            now,
            last_heartbeat
        ) > HEARTBEAT_INTERVAL:

            send_status()

            last_heartbeat = now

        time.sleep(0.1)

    except Exception as e:

        print("Error:", e)

        blink(5)

        time.sleep(2)

        machine.reset()