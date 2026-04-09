from umqtt.simple import MQTTClient
import ujson
import time

from config import MQTT_BROKER, NODE_ID
from worker import run_task

client = None


def on_message(topic, msg):

    topic = topic.decode()

    if topic == "cluster/task/" + NODE_ID:

        print("Task received")

        data = ujson.loads(msg)

        result = run_task(data)

        send_result(result)


def send_result(result):

    topic = "cluster/result/" + NODE_ID

    payload = ujson.dumps({

        "node": NODE_ID,
        "result": result

    })

    client.publish(topic, payload)


def register_node():

    payload = ujson.dumps({

        "node": NODE_ID,
        "status": "online"

    })

    client.publish("cluster/register", payload)


def connect():

    global client

    client = MQTTClient(NODE_ID, MQTT_BROKER)

    client.set_callback(on_message)

    client.connect()

    client.subscribe("cluster/task/" + NODE_ID)

    print("MQTT connected")

    register_node()


connect()

while True:

    try:

        client.check_msg()

        time.sleep(0.1)

    except:

        connect()