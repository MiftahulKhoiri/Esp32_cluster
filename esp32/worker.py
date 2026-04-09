import random

def run_task(data):

    count = data.get("count", 10)

    result = []

    for i in range(count):

        number = random.randint(1, 6)

        result.append(number)

    return result