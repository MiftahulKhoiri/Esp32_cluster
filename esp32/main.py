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

last_heartbeat = 0


# =========================
# TASK STATUS (ACK)
# =========================

def send_task_status(task_id, status):

    try:

        payload = ujson.dumps({

            "node": NODE_ID,
            "task_id": task_id,
            "status": status,
            "timestamp": time.time()

        })

        topic = "cluster/task_status/" + NODE_ID

        client.publish(
            topic,
            payload
        )

    except Exception as e:

        print("Task status error:", e)


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
            led.set_state(
                led.STATE_READY
            )

        print("Node READY")

    except Exception as e:

        print("Ready state error:", e)


# =========================
# OTA HANDLER (NEW)
# =========================

def handle_ota_command():

    print("OTA command received")

    if LED_AVAILABLE:
        led.set_state(
            led.STATE_OTA
        )

    try:

        ota.perform_update()

    except Exception as e:

        print("OTA update failed:", e)

        if LED_AVAILABLE:
            led.set_state(
                led.STATE_ERROR
            )


# =========================
# MESSAGE HANDLER
# =========================

def on_message(topic, msg):

    try:

        topic = topic.decode()

        # ---------------------
        # OTA COMMAND
        # ---------------------

        if topic == "cluster/ota/update":

            handle_ota_command()

            return

        # ---------------------
        # TASK COMMAND
        # ---------------------

        if topic == "cluster/task/" + NODE_ID:

            print("Task received")

            data = ujson.loads(msg)

            task_id = data.get(
                "task_id",
                "unknown"
            )

            # ACK: RECEIVED

            send_task_status(
                task_id,
                "received"
            )

            if LED_AVAILABLE:
                led.set_state(
                    led.STATE_RUNNING
                )

            # ACK: RUNNING

            send_task_status(
                task_id,
                "running"
            )

            # RUN TASK

            result = run_task(data)

            send_result(result)

            # FINAL STATUS

            final_status = result.get(
                "status",
                "done"
            )

            send_task_status(
                task_id,
                final_status
            )

            # BACK TO READY

            set_ready_state()

    except Exception as e:

        print("Task error:", e)

        send_task_status(
            "unknown",
            "error"
        )

        if LED_AVAILABLE:
            led.set_state(
                led.STATE_ERROR
            )


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

        client.publish(
            topic,
            payload
        )

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
                led.set_state(
                    led.STATE_WIFI
                )

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

            # SUBSCRIBE TOPICS

            client.subscribe(
                "cluster/task/" + NODE_ID
            )

            client.subscribe(
                "cluster/ota/update"
            )

            print("MQTT connected")

            register_node()

            set_ready_state()

            return

        except Exception as e:

            print("MQTT connect failed:", e)

            if LED_AVAILABLE:
                led.set_state(
                    led.STATE_ERROR
                )

            time.sleep(5)


# =========================
# HEARTBEAT
# =========================

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

    except Exception as e:

        print("Heartbeat error:", e)


# =========================
# MAIN LOOP
# =========================

def main():

    print("Booting node:", NODE_ID)

    if LED_AVAILABLE:
        led.set_state(
            led.STATE_WIFI
        )

    # 1) CONNECT WIFI

    connect_wifi()

    time.sleep(2)

    # 2) OTA CHECK ON BOOT

    try:

        ota.perform_update()

    except Exception as e:

        print("OTA error:", e)

    # 3) CONNECT MQTT

    connect_mqtt()

    # 4) MAIN LOOP

    while True:

        try:

            ensure_connection()

            client.check_msg()

            send_heartbeat()

        except Exception as e:

            print("MQTT error:", e)

            if LED_AVAILABLE:
                led.set_state(
                    led.STATE_ERROR
                )

            time.sleep(2)

            connect_mqtt()

        time.sleep(0.1)


# =========================

main()