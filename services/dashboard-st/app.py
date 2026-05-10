import streamlit as st
import sqlite3
import pandas as pd
import json
import os
import time

st.set_page_config(page_title="CardioTwin Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Inject premium custom CSS
st.markdown("""
<style>
    /* Premium Dark Mode Styling */
    .stApp {
        background-color: #0d1322;
        color: #e6ebf2;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide top header and default UI elements */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .stMetric {
        background: linear-gradient(180deg, rgba(19,27,46,0.7), rgba(17,24,39,0.55));
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s, border-color 0.2s;
    }
    .stMetric:hover {
        transform: translateY(-2px);
        border-color: #374151;
    }
    .stMetric label {
        color: #8b95a8 !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.8rem;
    }
    .stMetric div[data-testid="stMetricValue"] {
        color: #e6ebf2;
        font-size: 2.2rem;
        font-weight: 700;
    }

    /* Risk Semaphore Styles */
    .risk-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: linear-gradient(180deg, rgba(19,27,46,0.72), rgba(17,24,39,0.55));
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 30px;
        box-shadow: 0 8px 24px -12px rgba(0,0,0,0.7);
        height: 100%;
    }
    .risk-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #e6ebf2;
        margin-bottom: 20px;
        letter-spacing: 1px;
    }
    .semaphore {
        display: flex;
        gap: 20px;
        margin-bottom: 20px;
    }
    .light {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        opacity: 0.2;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    .light.green { background-color: #10b981; }
    .light.yellow { background-color: #f59e0b; }
    .light.red { background-color: #ef4444; }
    
    .light.active {
        opacity: 1;
        box-shadow: 0 0 20px 5px currentColor;
        transform: scale(1.1);
    }
    .light.active.green { border-color: #059669; color: #10b981; }
    .light.active.yellow { border-color: #d97706; color: #f59e0b; }
    .light.active.red { border-color: #dc2626; color: #ef4444; }

    .risk-value {
        font-size: 3rem;
        font-weight: 700;
        margin-top: 10px;
    }
    .risk-value.green { color: #10b981; }
    .risk-value.yellow { color: #f59e0b; }
    .risk-value.red { color: #ef4444; }
    
    h1 {
        color: #e6ebf2;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 2rem;
        text-align: center;
        background: -webkit-linear-gradient(#eee, #333);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)


DB_PATH = os.getenv("DB_PATH", "/data/cardiotwin.db")

def _query(sql: str, params: tuple = ()) -> list[dict]:
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        rows = []
    finally:
        conn.close()
    return [dict(r) for r in rows]

def _has_column(table: str, column: str) -> bool:
    cols = _query(f"PRAGMA table_info({table})")
    return any(c["name"] == column for c in cols)

def fetch_data():
    glucose_col = ", glucose" if _has_column("telemetry", "glucose") else ""
    telemetry = _query(
        f"SELECT patient_id, sysBP, diaBP, heartRate{glucose_col}, timestamp "
        "FROM telemetry ORDER BY id DESC LIMIT 1"
    )
    predictions = _query(
        "SELECT patient_id, risk_pct, shap_json, timestamp "
        "FROM predictions ORDER BY id DESC LIMIT 1"
    )
    return telemetry[0] if telemetry else None, predictions[0] if predictions else None

# Fetch data
latest_t, latest_p = fetch_data()

st.markdown("<h1 style='text-align: center;'>CardioTwin Digital Dashboard</h1>", unsafe_allow_html=True)

if not latest_t and not latest_p:
    st.warning("No data available yet. Waiting for telemetry...")
else:
    # ------------------------- VITAL SIGNS -------------------------
    st.markdown("### Latest Vital Signs")
    col1, col2, col3, col4 = st.columns(4)
    
    if latest_t:
        col1.metric("Systolic BP (mmHg)", f"{latest_t.get('sysBP', '--'):.1f}")
        col2.metric("Diastolic BP (mmHg)", f"{latest_t.get('diaBP', '--'):.1f}")
        col3.metric("Heart Rate (bpm)", f"{latest_t.get('heartRate', '--'):.1f}")
        glucose_val = latest_t.get('glucose')
        col4.metric("Glucose", f"{glucose_val:.1f}" if glucose_val is not None else "--")

    st.write("---")

    # ------------------------- RISK & SHAP -------------------------
    col_risk, col_shap = st.columns([1, 2])

    with col_risk:
        st.markdown("### Cardiovascular Risk")
        
        if latest_p and latest_p.get('risk_pct') is not None:
            risk_pct = float(latest_p['risk_pct']) * 100
            
            # Determine status
            status_green = "active" if risk_pct < 20 else ""
            status_yellow = "active" if 20 <= risk_pct <= 50 else ""
            status_red = "active" if risk_pct > 50 else ""
            
            color_class = "green" if risk_pct < 20 else "yellow" if risk_pct <= 50 else "red"
            
            html_code = f"""
            <div class="risk-container">
                <div class="risk-title">Risk Assessment Semaphore</div>
                <div class="semaphore">
                    <div class="light green {status_green}"></div>
                    <div class="light yellow {status_yellow}"></div>
                    <div class="light red {status_red}"></div>
                </div>
                <div class="risk-value {color_class}">{risk_pct:.1f}%</div>
                <div style="color: #8b95a8; font-size: 0.9rem; margin-top: 10px;">Predicted Probability</div>
            </div>
            """
            st.markdown(html_code, unsafe_allow_html=True)
        else:
            st.info("Awaiting predictions...")

    with col_shap:
        st.markdown("### Most Influential Variables (SHAP)")
        
        if latest_p and latest_p.get('shap_json'):
            try:
                shap_dict = json.loads(latest_p['shap_json'])
                # Convert to dataframe for chart
                df_shap = pd.DataFrame(list(shap_dict.items()), columns=['Feature', 'Impact'])
                # Sort by absolute impact to show the most important ones
                df_shap['AbsImpact'] = df_shap['Impact'].abs()
                df_shap = df_shap.sort_values('AbsImpact', ascending=True).tail(10) # top 10 features
                
                # Streamlit bar chart horizontal workaround (or just vertical if using st.bar_chart)
                # Streamlit's native st.bar_chart is vertical. We can use it directly by setting Feature as index.
                # However, a horizontal bar chart looks better for feature importance.
                # Since we don't have Plotly guaranteed, we can use altair or simple st.bar_chart.
                
                chart_data = df_shap.set_index('Feature')[['Impact']]
                st.bar_chart(chart_data, color="#e53e3e")
                
            except Exception as e:
                st.error(f"Error parsing SHAP data: {e}")
        else:
            st.info("Awaiting SHAP values...")

    st.caption(f"Last updated: {latest_p.get('timestamp') if latest_p else latest_t.get('timestamp')}")

# Auto-refresh loop
time.sleep(0.5)
st.rerun()
