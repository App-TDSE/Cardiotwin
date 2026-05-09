import json
import os
import sqlite3
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

DB_PATH = os.getenv("DB_PATH", "/data/cardiotwin.db")
INDEX_PATH = os.getenv("INDEX_PATH", "/app/static/index.html")
HISTORY_LEN = int(os.getenv("HISTORY_LEN", "60"))

app = FastAPI(title="CardioTwin Dashboard")


def _query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return [dict(r) for r in rows]


def _has_column(table: str, column: str) -> bool:
    cols = _query(f"PRAGMA table_info({table})")
    return any(c["name"] == column for c in cols)


@app.get("/api/state")
def state():
    glucose_col = ", glucose" if _has_column("telemetry", "glucose") else ""

    telemetry = _query(
        f"SELECT patient_id, sysBP, diaBP, heartRate{glucose_col}, timestamp "
        "FROM telemetry ORDER BY id DESC LIMIT ?",
        (HISTORY_LEN,),
    )
    predictions = _query(
        "SELECT patient_id, risk_pct, shap_json, timestamp "
        "FROM predictions ORDER BY id DESC LIMIT ?",
        (HISTORY_LEN,),
    )

    latest_t = telemetry[0] if telemetry else {}
    latest_p = predictions[0] if predictions else {}

    shap_dict: dict[str, float] = {}
    if latest_p.get("shap_json"):
        try:
            shap_dict = json.loads(latest_p["shap_json"])
        except Exception:
            shap_dict = {}

    risk_pct_raw = latest_p.get("risk_pct")
    risk_pct = float(risk_pct_raw) * 100 if risk_pct_raw is not None else None

    return {
        "patient_id": latest_p.get("patient_id") or latest_t.get("patient_id"),
        "vitals": {
            "sys": latest_t.get("sysBP"),
            "dia": latest_t.get("diaBP"),
            "hr": latest_t.get("heartRate"),
            "glu": latest_t.get("glucose"),
        },
        "vitals_history": list(reversed(telemetry)),
        "risk_pct": risk_pct,
        "risk_history": [
            {
                "risk_pct": (float(r["risk_pct"]) * 100) if r["risk_pct"] is not None else None,
                "timestamp": r["timestamp"],
            }
            for r in reversed(predictions)
        ],
        "shap": [{"name": k, "impact": float(v)} for k, v in shap_dict.items()],
        "timestamp": latest_p.get("timestamp") or latest_t.get("timestamp"),
    }


@app.get("/api/health")
def health():
    return JSONResponse(
        {
            "ok": True,
            "db": os.path.exists(DB_PATH),
            "db_path": DB_PATH,
        }
    )


@app.get("/")
def root():
    return FileResponse(INDEX_PATH)
