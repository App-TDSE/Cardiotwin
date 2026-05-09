import paho.mqtt.client as mqtt
import pandas as pd
import time
import json
import os

# Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = 1883
MQTT_TOPIC = "cardiotwin/data"
DATA_PATH = "../../data/framingham.csv"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

client = mqtt.Client()
client.on_connect = on_connect

while True:
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        break
    except:
        print("Waiting for broker...")
        time.sleep(2)

df = pd.read_csv(DATA_PATH)

print("Starting emulation...")
while True:
    for _, row in df.iterrows():
        payload = row.to_dict()
        client.publish(MQTT_TOPIC, json.dumps(payload))
        print(f"Published: {payload['TenYearCHD']}")
        time.sleep(5)
