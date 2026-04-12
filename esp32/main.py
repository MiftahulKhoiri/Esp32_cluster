from umqtt.simple import MQTTClient
import ujson
import time
import machine

from config import (
    MQTT_BROKER,
    NODE_ID,
    HEARTBEAT_INTERVAL
)

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
# SAFE RESULT SEND
# =========================

def send_result(result):

    try:

        topic = "cluster/result/" + NODE_ID

        payload = ujson.dumps({

            "node": NODE_ID,
            "result": result

        })

        # protect large payload

        if len(payload) > 50000:

            print("Result too large")

            result = {

                "status": "error",
                "message": "result too large"

            }

            payload = ujson.dumps({

                "node": NODE_ID,
                "result": result

            })

        client.publish(
            topic,
            payload
        )

    except Exception as e:

        print(
            "Send result error:",
            e
        )


# =========================
# TASK STATUS
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

        print(
            "Task status error:",
            e
        )


# =========================
# READY
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

        print("Ready error:", e)


# =========================
# OTA
# =========================

def handle_ota_command():

    print("OTA command received")

    if LED_AVAILABLE:

        led.set_state(
            led.STATE_OTA
        )

    ota.perform_update()


# =========================
# MESSAGE
# =========================

def on_message(topic, msg):

    try:

        topic = topic.decode()

        # OTA

        if topic == "cluster/ota/update":

            handle_ota_command()

            return

        # TASK

        if topic == "cluster/task/" + NODE_ID:

            print("Task received")

            data = ujson.loads(msg)

            task_id = data.get(
                "task_id",
                "unknown"
            )

            send_task_status(
                task_id,
                "received"
            )

            if LED_AVAILABLE:

                led.set_state(
                    led.STATE_RUNNING
                )

            send_task_status(
                task_id,
                "running"
            )

            # =========================
            # RUN TASK SAFE
            # =========================

            try:

                result = run_task(data)

            except Exception as e:

                print("Task crash:", e)

                result = {

                    "status": "error",
                    "message": str(e)

                }

            send_result(result)

            final_status = result.get(
                "status",
                "done"
            )

            send_task_status(
                task_id,
                final_status
            )

            set_ready_state()

    except Exception as e:

        print("Task error:", e)

        send_task_status(
            "unknown",
            "error"
        )


# =========================
# REGISTER
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

            client.set_callback(
                on_message
            )

            client.connect()

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

            print("MQTT failed:", e)

            time.sleep(5)


# =========================
# HEARTBEAT
# =========================

def send_heartbeat():

    global last_heartbeat

    now = time.time()

    if now - last_heartbeat < HEARTBEAT_INTERVAL:

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
# MAIN
# =========================

def main():

    print("Booting node:", NODE_ID)

    if LED_AVAILABLE:

        led.set_state(
            led.STATE_WIFI
        )

    connect_wifi()

    time.sleep(2)

    # OTA CHECK

    try:

        ota.perform_update()

    except Exception as e:

        print("OTA error:", e)

    connect_mqtt()

    while True:

        try:

            ensure_connection()

            client.check_msg()

            send_heartbeat()

        except Exception as e:

            print("MQTT error:", e)

            time.sleep(2)

            connect_mqtt()

        time.sleep(0.1)


main()