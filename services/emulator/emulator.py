import json
import os
import time
import math

import numpy as np
import pandas as pd
import paho.mqtt.client as mqtt

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC_RAW", "cardiotwin/telemetry/raw")
DATASET_PATH = os.getenv("DATASET_PATH", "/data/framingham.csv")
PUBLISH_INTERVAL = float(os.getenv("PUBLISH_INTERVAL", "1.0"))
NOISE_MU = float(os.getenv("NOISE_MU", "0.0"))
NOISE_SIGMA = float(os.getenv("NOISE_SIGMA", "2.0"))

NOISY_FIELDS = ("sysBP", "diaBP", "heartRate")


def on_connect(client, userdata, flags, rc):
    print(f"[emulator] connected to MQTT broker rc={rc}", flush=True)


def clean(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def main():
    rng = np.random.default_rng()

    df = pd.read_csv(DATASET_PATH)
    print(f"[emulator] loaded {len(df)} rows from {DATASET_PATH}", flush=True)

    client = mqtt.Client()
    client.on_connect = on_connect

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except Exception as exc:
            print(f"[emulator] waiting for broker ({exc})", flush=True)
            time.sleep(2)

    client.loop_start()

    print(
        f"[emulator] publishing to '{MQTT_TOPIC}' every {PUBLISH_INTERVAL}s "
        f"with noise N(mu={NOISE_MU}, sigma={NOISE_SIGMA}) on {NOISY_FIELDS}",
        flush=True,
    )

    try:
        for idx, row in df.iterrows():
            payload = {k: clean(v) for k, v in row.to_dict().items()}

            for field in NOISY_FIELDS:
                base = payload.get(field)
                if base is None:
                    continue
                noisy = float(base) + float(rng.normal(NOISE_MU, NOISE_SIGMA))
                payload[field] = round(noisy, 2)

            payload["patient_id"] = int(idx)
            payload["timestamp"] = time.time()

            client.publish(MQTT_TOPIC, json.dumps(payload))
            print(
                f"[emulator] #{idx} sysBP={payload.get('sysBP')} "
                f"diaBP={payload.get('diaBP')} hr={payload.get('heartRate')}",
                flush=True,
            )
            time.sleep(PUBLISH_INTERVAL)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
