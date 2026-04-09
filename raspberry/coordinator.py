import json
import time

import paho.mqtt.client as mqtt

from config import MQTT_BROKER


# =========================
# STATE
# =========================

ready_nodes = set()


# =========================
# MQTT CONNECT
# =========================

def on_connect(client, userdata, flags, rc):

    print("Server connected")

    client.subscribe("cluster/status/+")
    client.subscribe("cluster/result/+")
    client.subscribe("cluster/task_status/+")


# =========================
# MESSAGE HANDLER
# =========================

def on_message(client, userdata, msg):

    topic = msg.topic

    payload = json.loads(msg.payload)

    # ---------------------
    # NODE STATUS
    # ---------------------

    if topic.startswith("cluster/status"):

        node = payload["node"]

        status = payload["status"]

        if status == "ready":

            ready_nodes.add(node)

            print("Node READY:", node)

        if status == "offline":

            ready_nodes.discard(node)

            print("Node OFFLINE:", node)

    # ---------------------
    # TASK RESULT
    # ---------------------

    if topic.startswith("cluster/result"):

        print("Result received")

        print(payload)

    # ---------------------
    # TASK STATUS (ACK)
    # ---------------------

    if topic.startswith("cluster/task_status"):

        print("Task status:", payload)


# =========================
# MQTT SETUP
# =========================

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER)

client.loop_start()


# =========================
# DEMO TASK LOOP
# =========================

while True:

    if ready_nodes:

        node = list(ready_nodes)[0]

        task = {

            "task_id": str(time.time()),

            "task": "random",

            "count": 10

        }

        topic = "cluster/task/" + node

        client.publish(

            topic,

            json.dumps(task)

        )

        print("Task sent to", node)

        time.sleep(5)

    else:

        print("Waiting for READY node")

        time.sleep(2)