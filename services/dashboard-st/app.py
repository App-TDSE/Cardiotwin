import streamlit as st
import sqlite3
import json
import os
import time
from datetime import datetime

st.set_page_config(
    page_title="CardioTwin Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
#  Theme — clones the .sl-* section from idea.html so the iframe at
#  /streamlit/ blends with the rest of index.html.
# ---------------------------------------------------------------------------
st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
:root {
  --bg: #0a0f1e;
  --bg-2: #0d1322;
  --surface: #111827;
  --surface-2: #131b2e;
  --border: #1f2937;
  --border-strong: #2a3548;
  --text: #e6ebf2;
  --text-dim: #8b95a8;
  --text-mute: #5b6577;
  --accent: #e53e3e;
  --cyan: #06b6d4;
  --green: #10b981;
  --amber: #f59e0b;
  --red: #ef4444;
  --radius: 8px;
  --radius-sm: 6px;
}

/* Streamlit chrome */
.stApp {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background-image:
    radial-gradient(700px 220px at 50% -10%, rgba(6,182,212,0.07), transparent 70%),
    radial-gradient(500px 300px at 100% 110%, rgba(229,62,62,0.05), transparent 70%);
}
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, header { visibility: hidden; height: 0; }
.block-container { padding: 18px 22px 28px !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }

/* Defeat Streamlit's default code-block coloring just in case */
pre, code { background: transparent !important; color: inherit !important; }

/* ===== Card wrapper ===== */
.sl-card {
  background: linear-gradient(180deg, rgba(19,27,46,0.72), rgba(17,24,39,0.55));
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px 26px 24px;
  box-shadow: 0 1px 0 rgba(255,255,255,0.02) inset, 0 8px 24px -12px rgba(0,0,0,0.7);
  position: relative;
  overflow: hidden;
  margin-bottom: 18px;
}
.sl-card::before {
  content: '';
  position: absolute; inset: 0;
  background:
    radial-gradient(700px 220px at 50% -10%, rgba(6,182,212,0.07), transparent 70%),
    radial-gradient(500px 300px at 100% 110%, rgba(229,62,62,0.05), transparent 70%);
  pointer-events: none;
}
.sl-card > * { position: relative; z-index: 1; }

/* ===== Header ===== */
.sl-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 24px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 22px;
}
.sl-title {
  margin: 0;
  font-size: 24px; font-weight: 700;
  letter-spacing: -0.02em; color: var(--text); line-height: 1.1;
}
.sl-title-accent { color: var(--text-dim); font-weight: 500; }
.sl-subtitle {
  margin: 6px 0 0; font-size: 12px;
  color: var(--text-mute); line-height: 1.4;
}
.sl-mono { font-family: 'JetBrains Mono', ui-monospace, monospace; }
.sl-head-meta { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.sl-head-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 10px;
  background: rgba(6,182,212,0.08);
  border: 1px solid rgba(6,182,212,0.28);
  color: #7dd3fc;
  border-radius: 999px;
  font-size: 10px; font-weight: 600;
  letter-spacing: 0.10em; text-transform: uppercase;
}
@keyframes heartbeat {
  0%, 100% { transform: scale(1); }
  20%      { transform: scale(1.18); }
  40%      { transform: scale(0.96); }
  60%      { transform: scale(1.08); }
}
.sl-pulse {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--cyan); box-shadow: 0 0 8px var(--cyan);
  animation: heartbeat 1.6s ease-in-out infinite;
}
.sl-head-time {
  font-size: 13px; color: var(--text-dim);
  letter-spacing: 0.04em;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

/* ===== Section blocks ===== */
.sl-block-title {
  font-size: 11px; font-weight: 600;
  letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--text-mute);
  margin: 0 0 12px 0;
  display: flex; align-items: baseline; gap: 8px;
}
.sl-block-sub {
  font-size: 10px; color: var(--text-mute);
  opacity: 0.7; letter-spacing: 0.10em;
}

/* ===== Vitals grid ===== */
.sl-vitals-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.sl-vital {
  background: rgba(13,19,34,0.6);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 12px 14px 14px;
  display: flex; flex-direction: column; gap: 6px;
  transition: border-color 200ms ease;
}
.sl-vital:hover { border-color: var(--border-strong); }
.sl-vital-label {
  font-size: 10px; font-weight: 600;
  letter-spacing: 0.10em; text-transform: uppercase;
  color: var(--text-mute);
}
.sl-vital-label .sl-unit {
  font-weight: 400; text-transform: none; letter-spacing: 0;
  color: var(--text-mute); opacity: 0.75; margin-left: 2px;
}
.sl-vital-value {
  font-size: 30px; font-weight: 700;
  letter-spacing: -0.02em; color: var(--text);
  line-height: 1; margin-top: 2px;
  font-variant-numeric: tabular-nums;
}
.sl-vital-bar {
  margin-top: 6px; height: 3px;
  background: rgba(255,255,255,0.04);
  border-radius: 2px; overflow: hidden;
}
.sl-vital-bar > i {
  display: block; height: 100%; border-radius: 2px;
  font-style: normal;
  transition: width 600ms cubic-bezier(.22,.61,.36,1);
}

/* ===== Split: risk + shap ===== */
.sl-split {
  margin-top: 22px; padding-top: 22px;
  border-top: 1px solid var(--border);
  display: grid;
  grid-template-columns: minmax(280px, 360px) 1fr;
  gap: 24px;
}
@media (max-width: 1100px) {
  .sl-vitals-grid { grid-template-columns: repeat(2, 1fr); }
  .sl-split { grid-template-columns: 1fr; }
}

/* ===== Semaphore ===== */
.sl-semaphore-card {
  background: rgba(13,19,34,0.6);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 18px 18px 22px;
  display: flex; flex-direction: column; gap: 14px;
  align-items: center; text-align: center;
}
.sl-semaphore-title {
  font-size: 12px; font-weight: 600;
  color: var(--text); letter-spacing: 0.04em;
}
.sl-semaphore { display: flex; align-items: center; gap: 22px; padding: 6px 4px 18px; }
.sl-light {
  position: relative;
  width: 44px; height: 44px; border-radius: 50%;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  transition: all 250ms ease;
}
.sl-light-low  { background: radial-gradient(circle at 35% 30%, #1a4a32, #102a1f 70%); border-color: rgba(16,185,129,0.18); }
.sl-light-mid  { background: radial-gradient(circle at 35% 30%, #4a3a1a, #2a2010 70%); border-color: rgba(245,158,11,0.18); }
.sl-light-high { background: radial-gradient(circle at 35% 30%, #4a1a1a, #2a1010 70%); border-color: rgba(229,62,62,0.20); }
.sl-light-low.active {
  background: radial-gradient(circle at 35% 30%, #34d399, #059669 70%);
  border-color: rgba(16,185,129,0.45);
  box-shadow: 0 0 18px 2px rgba(16,185,129,0.55), 0 0 0 1px rgba(16,185,129,0.4) inset;
}
.sl-light-mid.active {
  background: radial-gradient(circle at 35% 30%, #fbbf24, #d97706 70%);
  border-color: rgba(245,158,11,0.55);
  box-shadow: 0 0 18px 2px rgba(245,158,11,0.55), 0 0 0 1px rgba(245,158,11,0.4) inset;
}
.sl-light-high.active {
  background: radial-gradient(circle at 35% 30%, #f87171, #dc2626 70%);
  border-color: rgba(239,68,68,0.55);
  box-shadow: 0 0 18px 2px rgba(239,68,68,0.55), 0 0 0 1px rgba(239,68,68,0.4) inset;
}
.sl-light-label {
  position: absolute; bottom: -16px; left: 50%; transform: translateX(-50%);
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 9px; color: var(--text-mute);
  letter-spacing: 0.10em; font-weight: 600;
}
.sl-light-low.active  .sl-light-label { color: #6ee7b7; }
.sl-light-mid.active  .sl-light-label { color: #fcd34d; }
.sl-light-high.active .sl-light-label { color: #fca5a5; }

.sl-prob { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.sl-prob-value {
  font-size: 44px; font-weight: 700; letter-spacing: -0.03em;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  color: #34d399;
  text-shadow: 0 0 24px rgba(16,185,129,0.45);
}
.sl-prob-value.mid  { color: #fbbf24; text-shadow: 0 0 24px rgba(245,158,11,0.45); }
.sl-prob-value.high { color: #f87171; text-shadow: 0 0 24px rgba(239,68,68,0.45); }
.sl-prob-pct { font-size: 22px; color: #6ee7b7; font-weight: 500; margin-left: 2px; }
.sl-prob-value.mid  .sl-prob-pct { color: #fcd34d; }
.sl-prob-value.high .sl-prob-pct { color: #fca5a5; }
.sl-prob-caption { font-size: 11px; color: var(--text-mute); letter-spacing: 0.06em; }

.sl-prob-meter {
  margin-top: 8px; width: 100%; height: 6px;
  background: rgba(255,255,255,0.04); border-radius: 3px;
  position: relative; overflow: hidden;
}
.sl-prob-meter-fill {
  position: absolute; left: 0; top: 0; bottom: 0;
  background: linear-gradient(90deg, #10b981, #34d399);
  box-shadow: 0 0 12px rgba(16,185,129,0.6);
  border-radius: 3px;
  transition: width 600ms cubic-bezier(.22,.61,.36,1);
}
.sl-prob-meter-fill.mid  { background: linear-gradient(90deg, #d97706, #fbbf24); box-shadow: 0 0 12px rgba(245,158,11,0.6); }
.sl-prob-meter-fill.high { background: linear-gradient(90deg, #dc2626, #f87171); box-shadow: 0 0 12px rgba(239,68,68,0.6); }
.sl-prob-meter-tick { position: absolute; top: -2px; bottom: -2px; width: 1px; background: var(--border-strong); }
.sl-prob-scale {
  width: 100%; display: flex; justify-content: space-between;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 9.5px; color: var(--text-mute);
  margin-top: 4px; letter-spacing: 0.04em;
}

/* ===== SHAP plot ===== */
.sl-shap {
  background: rgba(13,19,34,0.6);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 18px 18px 14px;
  position: relative;
  height: 260px;
  display: flex;
  flex-direction: column;
}
.sl-shap-plot {
  position: relative;
  flex: 1;
  margin-bottom: 26px;
}
.sl-shap-plot::before {
  content: ''; position: absolute; inset: 0;
  background: repeating-linear-gradient(0deg, transparent 0, transparent calc(20% - 1px), rgba(255,255,255,0.05) calc(20% - 1px), rgba(255,255,255,0.05) 20%);
  pointer-events: none;
}
.sl-shap-bars {
  position: absolute; inset: 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
  align-items: end;
}
.sl-shap-col {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
}
.sl-shap-bar {
  width: 100%; max-width: 110px;
  background: linear-gradient(180deg, rgba(6,182,212,0.85), rgba(6,182,212,0.55));
  border: 1px solid rgba(6,182,212,0.5);
  border-bottom: none;
  border-radius: 4px 4px 0 0;
  box-shadow: 0 0 18px -4px rgba(6,182,212,0.55);
  position: relative;
  transition: height 600ms cubic-bezier(.22,.61,.36,1);
}
.sl-shap-bar.pos {
  background: linear-gradient(180deg, rgba(229,62,62,0.85), rgba(229,62,62,0.55));
  border-color: rgba(229,62,62,0.5);
  box-shadow: 0 0 18px -4px rgba(229,62,62,0.55);
}
.sl-shap-bar-val {
  position: absolute; top: -18px; left: 50%; transform: translateX(-50%);
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 11px; color: #7dd3fc; font-weight: 600; letter-spacing: 0.02em;
  white-space: nowrap;
}
.sl-shap-bar.pos .sl-shap-bar-val { color: #fca5a5; }
.sl-shap-xlabel {
  position: absolute; bottom: -22px; left: 50%; transform: translateX(-50%);
  font-size: 11px; color: var(--text-dim); font-weight: 500; white-space: nowrap;
}
.sl-shap-foot {
  margin-top: 10px; font-size: 11px; color: var(--text-mute);
  display: flex; align-items: center; gap: 18px; flex-wrap: wrap;
}
.sl-shap-key { display: inline-flex; align-items: center; gap: 8px; }
.sl-shap-swatch {
  width: 10px; height: 10px; border-radius: 2px;
  background: linear-gradient(180deg, rgba(6,182,212,0.85), rgba(6,182,212,0.55));
}
.sl-shap-swatch.pos { background: linear-gradient(180deg, rgba(229,62,62,0.85), rgba(229,62,62,0.55)); }
.sl-empty { color: var(--text-mute); font-size: 12px; font-style: italic; padding: 14px; }
</style>
""",
    unsafe_allow_html=True,
)


DB_PATH = os.getenv("DB_PATH", "/data/cardiotwin.db")

SHAP_LABELS = {
    "sysBP": "Presión sistólica", "diaBP": "Presión diastólica",
    "heartRate": "Frec. cardíaca", "glucose": "Glucosa",
    "totChol": "Colesterol total", "age": "Edad", "BMI": "IMC",
    "cigsPerDay": "Cigarrillos/día", "male": "Sexo (M)",
    "education": "Educación", "currentSmoker": "Fumador",
    "BPMeds": "Medicación HTA", "prevalentStroke": "ACV previo",
    "prevalentHyp": "Hipertensión previa", "diabetes": "Diabetes",
}

VITAL_RANGES = {
    "sysBP": (80, 200), "diaBP": (50, 130),
    "heartRate": (40, 140), "glucose": (60, 300),
}

VITAL_COLORS = {
    "sysBP": "#e53e3e", "diaBP": "#fb923c",
    "heartRate": "#f87171", "glucose": "#06b6d4",
}


def _query(sql: str, params: tuple = ()):
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


def _has_column(table, column):
    return any(c["name"] == column for c in _query(f"PRAGMA table_info({table})"))


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
    return (telemetry[0] if telemetry else None,
            predictions[0] if predictions else None)


def scale_pct(value, key):
    lo, hi = VITAL_RANGES.get(key, (0, 1))
    if value is None:
        return 0
    span = hi - lo or 1
    return max(0, min(100, ((float(value) - lo) / span) * 100))


def vital_html(label, value, unit, key):
    if value is None:
        val_txt, pct = "—", 0
    else:
        val_txt = f"{float(value):.1f}"
        pct = scale_pct(float(value), key)
    color = VITAL_COLORS.get(key, "#06b6d4")
    return (
        '<div class="sl-vital">'
        f'<div class="sl-vital-label">{label} <span class="sl-unit">({unit})</span></div>'
        f'<div class="sl-vital-value">{val_txt}</div>'
        f'<div class="sl-vital-bar"><i style="width:{pct:.1f}%; background:{color}; box-shadow:0 0 10px -2px {color};"></i></div>'
        '</div>'
    )


def semaphore_html(risk_pct):
    if risk_pct is None:
        return (
            '<div class="sl-semaphore-card">'
            '<div class="sl-semaphore-title">Risk Assessment Semaphore</div>'
            '<div class="sl-empty">Awaiting predictions…</div>'
            '</div>'
        )
    if risk_pct < 20:
        level = "low"
    elif risk_pct < 50:
        level = "mid"
    else:
        level = "high"

    cls_low  = "active" if level == "low"  else ""
    cls_mid  = "active" if level == "mid"  else ""
    cls_high = "active" if level == "high" else ""
    prob_cls = "" if level == "low" else level
    fill_cls = "" if level == "low" else level

    return (
        '<div class="sl-semaphore-card">'
        '<div class="sl-semaphore-title">Risk Assessment Semaphore</div>'
        '<div class="sl-semaphore">'
        f'<div class="sl-light sl-light-low {cls_low}"><span class="sl-light-label">LOW</span></div>'
        f'<div class="sl-light sl-light-mid {cls_mid}"><span class="sl-light-label">MOD</span></div>'
        f'<div class="sl-light sl-light-high {cls_high}"><span class="sl-light-label">HIGH</span></div>'
        '</div>'
        '<div class="sl-prob">'
        f'<div class="sl-prob-value {prob_cls}">{risk_pct:.1f}<span class="sl-prob-pct">%</span></div>'
        '<div class="sl-prob-caption">Predicted Probability</div>'
        '</div>'
        '<div class="sl-prob-meter">'
        f'<div class="sl-prob-meter-fill {fill_cls}" style="width:{min(risk_pct,100):.1f}%;"></div>'
        '<div class="sl-prob-meter-tick" style="left:20%;"></div>'
        '<div class="sl-prob-meter-tick" style="left:50%;"></div>'
        '</div>'
        '<div class="sl-prob-scale"><span>0%</span><span>20%</span><span>50%</span><span>100%</span></div>'
        '</div>'
    )


def shap_html(shap_dict):
    if not shap_dict:
        return (
            '<div class="sl-shap"><div class="sl-empty" style="margin:auto;">Awaiting SHAP values…</div></div>'
            '<div class="sl-shap-foot">'
            '<span class="sl-shap-key"><span class="sl-shap-swatch pos"></span>Aumenta el riesgo</span>'
            '<span class="sl-shap-key"><span class="sl-shap-swatch"></span>Disminuye el riesgo</span>'
            '</div>'
        )

    items = sorted(shap_dict.items(), key=lambda kv: abs(float(kv[1])), reverse=True)[:3]
    max_abs = max(abs(float(v)) for _, v in items) or 1.0

    cols = []
    for name, val in items:
        v = float(val)
        h_pct = max(6.0, min(95.0, (abs(v) / max_abs) * 90))
        sign = "+" if v >= 0 else "−"
        cls = "pos" if v >= 0 else ""
        label = SHAP_LABELS.get(name, name)
        cols.append(
            '<div class="sl-shap-col">'
            f'<div class="sl-shap-bar {cls}" style="height:{h_pct:.1f}%;">'
            f'<span class="sl-shap-bar-val">{sign}{abs(v):.2f}</span>'
            '</div>'
            f'<div class="sl-shap-xlabel">{label}</div>'
            '</div>'
        )

    return (
        '<div class="sl-shap">'
        '<div class="sl-shap-plot">'
        f'<div class="sl-shap-bars">{"".join(cols)}</div>'
        '</div>'
        '</div>'
        '<div class="sl-shap-foot">'
        '<span class="sl-shap-key"><span class="sl-shap-swatch pos"></span>Aumenta el riesgo</span>'
        '<span class="sl-shap-key"><span class="sl-shap-swatch"></span>Disminuye el riesgo</span>'
        '</div>'
    )


# ----------------------------- RENDER --------------------------------------
latest_t, latest_p = fetch_data()

patient_id = (latest_p or {}).get("patient_id") or (latest_t or {}).get("patient_id")
patient_label = f"DT-{str(patient_id).zfill(4)}" if patient_id is not None else "DT-—"
now_str = datetime.now().strftime("%H:%M:%S")

risk_pct = None
if latest_p and latest_p.get("risk_pct") is not None:
    risk_pct = float(latest_p["risk_pct"]) * 100

shap_dict = None
if latest_p and latest_p.get("shap_json"):
    try:
        shap_dict = json.loads(latest_p["shap_json"])
    except Exception:
        shap_dict = None

if not latest_t and not latest_p:
    st.markdown(
        '<div class="sl-card"><div class="sl-empty">No data available yet. Waiting for telemetry…</div></div>',
        unsafe_allow_html=True,
    )
else:
    sys_v = (latest_t or {}).get("sysBP")
    dia_v = (latest_t or {}).get("diaBP")
    hr_v  = (latest_t or {}).get("heartRate")
    glu_v = (latest_t or {}).get("glucose")

    # Build the entire card as a single line-free string so Streamlit's
    # markdown renderer never sees indented blocks (which it would treat as
    # code).  Every chunk is concatenated below.
    html = "".join([
        '<div class="sl-card">',
          '<header class="sl-head">',
            '<div>',
              '<h2 class="sl-title">CardioTwin <span class="sl-title-accent">Digital Dashboard</span></h2>',
              f'<p class="sl-subtitle">Snapshot del último ciclo de inferencia · paciente virtual <span class="sl-mono">{patient_label}</span></p>',
            '</div>',
            '<div class="sl-head-meta">',
              '<span class="sl-head-badge"><span class="sl-pulse"></span>streaming</span>',
              f'<span class="sl-head-time">{now_str}</span>',
            '</div>',
          '</header>',
          '<div class="sl-block-title">Latest Vital Signs</div>',
          '<div class="sl-vitals-grid">',
            vital_html("Systolic BP",  sys_v, "mmHg",  "sysBP"),
            vital_html("Diastolic BP", dia_v, "mmHg",  "diaBP"),
            vital_html("Heart Rate",   hr_v,  "bpm",   "heartRate"),
            vital_html("Glucose",      glu_v, "mg/dL", "glucose"),
          '</div>',
          '<div class="sl-split">',
            '<div>',
              '<div class="sl-block-title">Cardiovascular Risk</div>',
              semaphore_html(risk_pct),
            '</div>',
            '<div>',
              '<div class="sl-block-title">Most Influential Variables <span class="sl-block-sub">(SHAP)</span></div>',
              shap_html(shap_dict),
            '</div>',
          '</div>',
        '</div>',
    ])

    st.markdown(html, unsafe_allow_html=True)

# Auto-refresh
time.sleep(1.0)
st.rerun()
