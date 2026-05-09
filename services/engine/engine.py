import paho.mqtt.client as mqtt
import pandas as pd
import joblib
import json
import os
import time

# Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = 1883
INPUT_TOPIC = "cardiotwin/data"
OUTPUT_TOPIC = "cardiotwin/results"
MODEL_PATH = "model.pkl"

model = joblib.load(MODEL_PATH)

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(INPUT_TOPIC)

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    df = pd.DataFrame([data]).drop('TenYearCHD', axis=1, errors='ignore')
    
    prediction = model.predict(df)[0]
    probability = model.predict_proba(df)[0][1]
    
    result = {
        "prediction": int(prediction),
        "probability": float(probability),
        "timestamp": time.time()
    }
    
    client.publish(OUTPUT_TOPIC, json.dumps(result))
    print(f"Processed prediction: {prediction}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

while True:
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        break
    except:
        print("Waiting for broker...")
        time.sleep(2)

client.loop_forever()
