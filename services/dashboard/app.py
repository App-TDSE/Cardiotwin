import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
import json

# Configuración
DB_PATH = os.getenv("DB_PATH", "/data/cardiotwin.db")

st.set_page_config(
    page_title="CardioTwin Digital Twin",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado para el semáforo y estética premium
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .risk-high { color: #ff4b4b; font-weight: bold; }
    .risk-med { color: #ffa500; font-weight: bold; }
    .risk-low { color: #00c853; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def get_data(query):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()

st.title("🫀 CardioTwin: Monitor de Gemelo Digital")
st.write("Visualización en tiempo real de riesgo coronario (CHD) a 10 años.")

# Layout principal
col_metrics, col_history = st.columns([1, 2])

# Obtener últimos datos de telemetría y predicciones
df_telemetry = get_data("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT 10")
df_predictions = get_data("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT 20")

with col_metrics:
    st.subheader("Signos Vitales (Real-time)")
    if not df_telemetry.empty:
        latest_t = df_telemetry.iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Presión Sistólica", f"{latest_t['sysBP']:.1f}", "mmHg")
        c2.metric("Presión Diastólica", f"{latest_t['diaBP']:.1f}", "mmHg")
        c3.metric("Frec. Cardíaca", f"{latest_t['heartRate']:.0f}", "bpm")
    else:
        st.info("Esperando datos de telemetría...")

    st.divider()
    
    st.subheader("Semáforo de Riesgo Coronario")
    if not df_predictions.empty:
        latest_p = df_predictions.iloc[0]
        risk = latest_p['risk_pct'] * 100
        
        if risk > 50:
            st.error(f"RIESGO ALTO: {risk:.1f}%")
        elif risk > 20:
            st.warning(f"RIESGO MODERADO: {risk:.1f}%")
        else:
            st.success(f"RIESGO BAJO: {risk:.1f}%")
            
        st.progress(min(risk/100, 1.0))
    else:
        st.info("Calculando predicciones iniciales...")

with col_history:
    st.subheader("Evolución del Riesgo")
    if not df_predictions.empty:
        fig = px.line(df_predictions, x='timestamp', y='risk_pct', 
                      title="Tendencia de Probabilidad de CHD",
                      labels={'risk_pct': 'Probabilidad', 'timestamp': 'Tiempo'})
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Gráfico de tendencia pendiente de datos...")

st.divider()

# Sección de Explicabilidad (SHAP)
st.subheader("🧠 Explicabilidad Clínica (Valores SHAP)")
if not df_predictions.empty:
    latest_shap = json.loads(df_predictions.iloc[0]['shap_json'])
    if latest_shap:
        # Convertir SHAP a DataFrame para visualización simple
        shap_df = pd.DataFrame(list(latest_shap.items()), columns=['Característica', 'Impacto'])
        shap_df = shap_df.sort_values(by='Impacto', ascending=False).head(5)
        fig_shap = px.bar(shap_df, x='Impacto', y='Característica', orientation='h',
                          title="Top 5 Factores que aumentan el riesgo actual",
                          color='Impacto', color_continuous_scale='Reds')
        st.plotly_chart(fig_shap, use_container_width=True)
    else:
        st.write("Cargando matriz de importancia...")
else:
    st.write("Los valores SHAP se mostrarán aquí una vez inicie el motor de inferencia.")

# Auto-refresh cada 1 segundo
st.empty()
time_placeholder = st.sidebar.empty()
import time
time.sleep(1)
st.rerun()
