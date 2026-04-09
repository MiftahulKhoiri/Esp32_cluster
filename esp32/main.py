from umqtt.simple import MQTTClient
import ujson
import time
import machine

from config import MQTT_BROKER, NODE_ID

from worker import run_task

from connectionwifi import (
    connect_wifi,
    ensure_connection
)

import ota

try:
    import led
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False


client = None


# =========================
# READY STATE
# =========================

def set_ready_state():

    try:

        payload = ujson.dumps({

            "node": NODE_ID,
            "status": "ready"

        })

        client.publish(

            "cluster/status/" + NODE_ID,
            payload

        )

        if LED_AVAILABLE:
            led.set_state(led.STATE_READY)

        print("Node READY")

    except Exception as e:

        print("Ready state error:", e)


# =========================
# MESSAGE HANDLER
# =========================

def on_message(topic, msg):

    try:

        topic = topic.decode()

        if topic == "cluster/task/" + NODE_ID:

            print("Task received")

            if LED_AVAILABLE:
                led.set_state(led.STATE_RUNNING)

            data = ujson.loads(msg)

            result = run_task(data)

            send_result(result)

            # kembali standby

            set_ready_state()

    except Exception as e:

        print("Task error:", e)

        if LED_AVAILABLE:
            led.set_state(led.STATE_ERROR)


# =========================
# SEND RESULT
# =========================

def send_result(result):

    try:

        topic = "cluster/result/" + NODE_ID

        payload = ujson.dumps({

            "node": NODE_ID,
            "result": result

        })

        client.publish(topic, payload)

    except Exception as e:

        print("Send result error:", e)


# =========================
# REGISTER NODE
# =========================

def register_node():

    payload = ujson.dumps({

        "node": NODE_ID,
        "status": "online"

    })

    client.publish(
        "cluster/register",
        payload
    )


# =========================
# MQTT CONNECT
# =========================

def connect_mqtt():

    global client

    while True:

        try:

            print("Connecting MQTT...")

            if LED_AVAILABLE:
                led.set_state(led.STATE_WIFI)

            if client:

                try:
                    client.disconnect()
                except:
                    pass

            client = MQTTClient(

                client_id=NODE_ID,
                server=MQTT_BROKER,
                keepalive=60

            )

            # Last Will

            client.set_last_will(

                topic="cluster/status/" + NODE_ID,

                msg=ujson.dumps({
                    "node": NODE_ID,
                    "status": "offline"
                }),

                retain=False

            )

            client.set_callback(on_message)

            client.connect()

            client.subscribe(

                "cluster/task/" + NODE_ID

            )

            print("MQTT connected")

            register_node()

            # masuk standby

            set_ready_state()

            return

        except Exception as e:

            print("MQTT connect failed:", e)

            if LED_AVAILABLE:
                led.set_state(led.STATE_ERROR)

            time.sleep(5)


# =========================
# HEARTBEAT
# =========================

last_heartbeat = 0

def send_heartbeat():

    global last_heartbeat

    now = time.time()

    if now - last_heartbeat < 30:
        return

    last_heartbeat = now

    try:

        payload = ujson.dumps({

            "node": NODE_ID,
            "status": "online"

        })

        client.publish(

            "cluster/status/" + NODE_ID,

            payload

        )

    except:

        pass


# =========================
# MAIN LOOP
# =========================

def main():

    print("Booting node:", NODE_ID)

    if LED_AVAILABLE:
        led.set_state(led.STATE_WIFI)

    # 1) CONNECT WIFI

    connect_wifi()

    time.sleep(2)

    # 2) OTA CHECK

    try:

        ota.perform_update()

    except Exception as e:

        print("OTA error:", e)

    # 3) CONNECT MQTT

    connect_mqtt()

    # 4) LOOP

    while True:

        try:

            ensure_connection()

            client.check_msg()

            send_heartbeat()

        except Exception as e:

            print("MQTT error:", e)

            if LED_AVAILABLE:
                led.set_state(led.STATE_ERROR)

            time.sleep(2)

            connect_mqtt()

        time.sleep(0.1)


# =========================

main()