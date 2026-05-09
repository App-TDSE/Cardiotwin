import paho.mqtt.client as mqtt
import sqlite3
import json
import os
import time

# Configuración
MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = 1883
DB_PATH = os.getenv("DB_PATH", "/data/cardiotwin.db")

# Tópicos a los que suscribirse
TOPICS = [
    "cardiotwin/telemetry/raw",
    "cardiotwin/telemetry/predictions"
]

def init_db():
    print(f"Inicializando base de datos en {DB_PATH}...")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla para predicciones (Requerimiento Estudiante C)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            patient_id TEXT,
            risk_pct REAL,
            shap_json TEXT
        )
    ''')
    
    # Tabla para signos vitales (Para el panel de telemetría)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            patient_id TEXT,
            sysBP REAL,
            diaBP REAL,
            heartRate REAL
        )
    ''')
    
    conn.commit()
    conn.close()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Watchdog conectado al broker MQTT")
        for topic in TOPICS:
            client.subscribe(topic)
            print(f"Suscrito a: {topic}")
    else:
        print(f"Error de conexión: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
        topic = msg.topic
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if topic == "cardiotwin/telemetry/predictions":
            cursor.execute('''
                INSERT INTO predictions (patient_id, risk_pct, shap_json)
                VALUES (?, ?, ?)
            ''', (
                payload.get('patient_id', 'unknown'),
                payload.get('risk_pct', 0.0),
                json.dumps(payload.get('shap_values', {}))
            ))
            
        elif topic == "cardiotwin/telemetry/raw":
            cursor.execute('''
                INSERT INTO telemetry (patient_id, sysBP, diaBP, heartRate)
                VALUES (?, ?, ?, ?)
            ''', (
                payload.get('patient_id', 'unknown'),
                payload.get('sysBP', 0.0),
                payload.get('diaBP', 0.0),
                payload.get('heartRate', 0.0)
            ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

if __name__ == "__main__":
    init_db()
    
    client = mqtt.Client("cardiotwin-watchdog")
    client.on_connect = on_connect
    client.on_message = on_message

    # Reintento de conexión inicial
    connected = False
    while not connected:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            connected = True
        except:
            print("Esperando al broker MQTT...")
            time.sleep(2)

    client.loop_forever()
