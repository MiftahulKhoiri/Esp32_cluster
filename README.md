# ESP32 Cluster

Distributed computing and machine learning cluster using:

- ESP32 (MicroPython)
- Raspberry Pi
- MQTT
- Edge Machine Learning

## Features

- Multi-node cluster
- Distributed training
- Heartbeat monitoring
- Task scheduling
- Machine learning pipeline

## Architecture

Raspberry Pi (Coordinator)
        |
      MQTT
        |
   ESP32 Nodes

## Run

### Start coordinator

python3 coordinator.py

### Start trainer

python3 trainer.py
