import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import plotly.express as px
import os

# Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_TOPIC = "cardiotwin/results"

st.set_page_config(page_title="Cardiotwin Dashboard", layout="wide")

st.title("🫀 Cardiotwin Real-time Dashboard")

if 'results' not in st.session_state:
    st.session_state.results = []

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    st.session_state.results.append(data)
    if len(st.session_state.results) > 50:
        st.session_state.results.pop(0)

@st.cache_resource
def get_mqtt_client():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, 1883, 60)
    client.subscribe(MQTT_TOPIC)
    client.loop_start()
    return client

client = get_mqtt_client()

# UI Layout
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Latest Prediction")
    if st.session_state.results:
        latest = st.session_state.results[-1]
        risk_color = "red" if latest['prediction'] == 1 else "green"
        st.markdown(f"### Risk: <span style='color:{risk_color}'>{'HIGH' if latest['prediction'] == 1 else 'LOW'}</span>", unsafe_allow_html=True)
        st.metric("Probability", f"{latest['probability']:.2%}")
    else:
        st.write("Waiting for data...")

with col2:
    st.subheader("Risk History")
    if st.session_state.results:
        df = pd.DataFrame(st.session_state.results)
        fig = px.line(df, y="probability", title="CHD Risk Probability Over Time")
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Raw Data Stream")
st.write(pd.DataFrame(st.session_state.results).tail(10))

# Refresh UI
st.button("Refresh Data")
