import paho.mqtt.client as mqtt
import json
import time

BROKER = "localhost"

TASK_TOPIC = "node/task"
RESULT_TOPIC = "node/result"
STATUS_TOPIC = "node/status"

task_counter = 0

# =============================
# DATASET
# =============================

dataset = [

    (1, 2),
    (2, 4),
    (3, 6),
    (4, 8)

]

# =============================
# MODEL PARAMETER
# =============================

a = 0.0
b = 0.0

learning_rate = 0.01

# =============================
# MQTT
# =============================

def send_task(command, value):

    global task_counter

    task_counter += 1

    task = {

        "task_id": task_counter,
        "command": command,
        "value": value

    }

    client.publish(
        TASK_TOPIC,
        json.dumps(task)
    )

def handle_result(data):

    global a, b

    result = data["result"]

    if "grad_a" in result:

        grad_a = result["grad_a"]
        grad_b = result["grad_b"]

        a -= learning_rate * grad_a
        b -= learning_rate * grad_b

        print(
            "MODEL:",
            "a =", round(a, 4),
            "b =", round(b, 4)
        )

def handle_status(data):

    print(
        "STATUS:",
        data["node"],
        "uptime:",
        data["uptime_ms"]
    )

def on_message(client, userdata, msg):

    data = json.loads(msg.payload)

    if msg.topic == RESULT_TOPIC:

        handle_result(data)

    elif msg.topic == STATUS_TOPIC:

        handle_status(data)

# =============================
# TRAIN STEP
# =============================

def train_step():

    for x, y in dataset:

        send_task(

            "train",

            {

                "x": x,
                "y": y,
                "a": a,
                "b": b

            }

        )

# =============================
# MQTT SETUP
# =============================

client = mqtt.Client()

client.on_message = on_message

client.connect(BROKER)

client.subscribe(RESULT_TOPIC)
client.subscribe(STATUS_TOPIC)

client.loop_start()

print("Training started...")

# =============================
# MAIN LOOP
# =============================

while True:

    train_step()

    time.sleep(2)