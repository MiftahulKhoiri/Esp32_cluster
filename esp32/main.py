from umqtt.simple import MQTTClient
import ujson
import time
import machine

from config import MQTT_BROKER, NODE_ID
from worker import run_task
from connectionwifi import connect_wifi
import ota

client = None


# =========================
# MESSAGE HANDLER
# =========================

def on_message(topic, msg):

    try:

        topic = topic.decode()

        if topic == "cluster/task/" + NODE_ID:

            print("Task received")

            data = ujson.loads(msg)

            result = run_task(data)

            send_result(result)

    except Exception as e:

        print("Task error:", e)


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

    client.publish("cluster/register", payload)


# =========================
# MQTT CONNECT
# =========================

def connect_mqtt():

    global client

    while True:

        try:

            print("Connecting MQTT...")

            client = MQTTClient(
                client_id=NODE_ID,
                server=MQTT_BROKER,
                keepalive=60
            )

            client.set_callback(on_message)

            client.connect()

            client.subscribe(
                "cluster/task/" + NODE_ID
            )

            print("MQTT connected")

            register_node()

            return

        except Exception as e:

            print("MQTT connect failed:", e)

            time.sleep(5)


# =========================
# MAIN LOOP
# =========================

def main():

    print("Booting node:", NODE_ID)

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

            client.check_msg()

        except Exception as e:

            print("MQTT error:", e)

            time.sleep(2)

            connect_mqtt()

        time.sleep(0.1)


# =========================

main()