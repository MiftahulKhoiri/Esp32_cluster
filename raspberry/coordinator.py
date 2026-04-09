import paho.mqtt.client as mqtt
import json
import time
import random

from config import MQTT_BROKER

nodes = set()

results = []


def on_connect(client, userdata, flags, rc):

    print("Connected")

    client.subscribe("cluster/register")

    client.subscribe("cluster/result/#")


def on_message(client, userdata, msg):

    topic = msg.topic
    payload = json.loads(msg.payload)

    if topic == "cluster/register":

        node = payload["node"]

        nodes.add(node)

        print("Node registered:", node)

    if topic.startswith("cluster/result"):

        print("Result received")

        results.append(payload)


client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER)

client.loop_start()


def wait_nodes():

    print("Waiting nodes...")

    while len(nodes) == 0:

        time.sleep(1)


def distribute_task():

    print("Distributing task")

    task = {

        "count": 100

    }

    for node in nodes:

        topic = "cluster/task/" + node

        client.publish(topic, json.dumps(task))


wait_nodes()

time.sleep(2)

distribute_task()

while True:

    time.sleep(1)