import json
import os
import time

import joblib
import pandas as pd
import paho.mqtt.client as mqtt
import shap
import sqlite3

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
INPUT_TOPIC = os.getenv("MQTT_TOPIC_RAW", "cardiotwin/telemetry/raw")
OUTPUT_TOPIC = os.getenv("MQTT_TOPIC_PRED", "cardiotwin/telemetry/predictions")
MODEL_PATH = os.getenv("MODEL_PATH", "/app/model.pkl")
DB_PATH = os.getenv("DB_PATH", "/data/cardiotwin.db")

print(f"[engine] loading model from {MODEL_PATH}", flush=True)
model = joblib.load(MODEL_PATH)
FEATURES = list(getattr(model, "feature_names_in_", []))

print("[engine] initializing SHAP explainer", flush=True)
explainer = shap.TreeExplainer(model)


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
        
        # Calculate SHAP values
        shap_vals = explainer.shap_values(df)
        if isinstance(shap_vals, list):
            sv = shap_vals[1][0]  # If list, index 1 is positive class
        else:
            sv = shap_vals[0]     # Typically array of shape (1, n_features)

        # Extract Top 3 SHAP features
        feature_importance = pd.DataFrame({
            'feature': df.columns,
            'importance': sv
        })
        feature_importance['abs_importance'] = feature_importance['importance'].abs()
        top_3 = feature_importance.sort_values(by='abs_importance', ascending=False).head(3)
        shap_dict = top_3.set_index('feature')['importance'].to_dict()

        result = {
            "patient_id": data.get("patient_id", "unknown"),
            "prediction": prediction,
            "risk_pct": probability, # Probability as 0-1 (can be multiplied by 100 later or here)
            "shap_values": shap_dict,
            "timestamp": time.time(),
        }
        
        # Publish to MQTT
        client.publish(OUTPUT_TOPIC, json.dumps(result))
        
        # Persist to SQLite
        try:
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    patient_id TEXT,
                    risk_pct REAL,
                    shap_json TEXT
                )
            ''')
            cursor.execute('''
                INSERT INTO predictions (patient_id, risk_pct, shap_json)
                VALUES (?, ?, ?)
            ''', (
                result["patient_id"],
                result["risk_pct"],
                json.dumps(result["shap_values"])
            ))
            conn.commit()
            conn.close()
        except Exception as db_err:
            print(f"[engine] database error: {db_err}", flush=True)

        print(
            f"[engine] patient={result['patient_id']} "
            f"risk_pct={probability:.3f} top_3_shap={list(shap_dict.keys())}",
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
