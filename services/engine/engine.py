import json
import os
import time

import joblib
import pandas as pd
import paho.mqtt.client as mqtt

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
INPUT_TOPIC = os.getenv("MQTT_TOPIC_RAW", "cardiotwin/telemetry/raw")
OUTPUT_TOPIC = os.getenv("MQTT_TOPIC_PRED", "cardiotwin/telemetry/predictions")
MODEL_PATH = os.getenv("MODEL_PATH", "/app/model.pkl")

print(f"[engine] loading model from {MODEL_PATH}", flush=True)
model = joblib.load(MODEL_PATH)
FEATURES = list(getattr(model, "feature_names_in_", []))


def on_connect(client, userdata, flags, rc):
    print(f"[engine] connected to MQTT broker rc={rc}", flush=True)
    client.subscribe(INPUT_TOPIC)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)
        df = pd.DataFrame([data])
        if FEATURES:
            df = df.reindex(columns=FEATURES)
        else:
            df = df.drop("TenYearCHD", axis=1, errors="ignore")

        prediction = int(model.predict(df)[0])
        probability = float(model.predict_proba(df)[0][1])

        result = {
            "patient_id": data.get("patient_id"),
            "prediction": prediction,
            "probability": probability,
            "timestamp": time.time(),
        }
        client.publish(OUTPUT_TOPIC, json.dumps(result))
        print(
            f"[engine] patient={result['patient_id']} "
            f"pred={prediction} prob={probability:.3f}",
            flush=True,
        )
    except Exception as exc:
        print(f"[engine] error processing message: {exc}", flush=True)


client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION1,
    client_id="cardiotwin-engine",
)
client.on_connect = on_connect
client.on_message = on_message

while True:
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        break
    except Exception as exc:
        print(f"[engine] waiting for broker ({exc})", flush=True)
        time.sleep(2)

client.loop_forever()
