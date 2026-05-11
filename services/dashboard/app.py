import json
import os
import sqlite3
from typing import Any, Optional

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

DB_PATH = os.getenv("DB_PATH", "/data/cardiotwin.db")
INDEX_PATH = os.getenv("INDEX_PATH", "/app/static/index.html")
MODEL_PATH = os.getenv("MODEL_PATH", "/data/model.pkl")
HISTORY_LEN = int(os.getenv("HISTORY_LEN", "60"))

app = FastAPI(title="CardioTwin Dashboard")

# ---- Lazy-loaded model + SHAP explainer (the engine writes the model
# to /data/model.pkl so we share it via the shared-data volume) ------------
_MODEL_CACHE: dict[str, Any] = {"model": None, "explainer": None, "features": None, "mtime": None}


def _ensure_model():
    """Load model + SHAP explainer once. Reload if file changed on disk."""
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(
            status_code=503,
            detail=f"Modelo aún no disponible en {MODEL_PATH}. Espera unos segundos.",
        )
    mtime = os.path.getmtime(MODEL_PATH)
    if _MODEL_CACHE["model"] is None or _MODEL_CACHE["mtime"] != mtime:
        import shap  # imported lazily to keep cold-start fast for /api/state

        model = joblib.load(MODEL_PATH)
        _MODEL_CACHE["model"] = model
        _MODEL_CACHE["features"] = list(getattr(model, "feature_names_in_", []))
        _MODEL_CACHE["explainer"] = shap.TreeExplainer(model)
        _MODEL_CACHE["mtime"] = mtime
    return _MODEL_CACHE["model"], _MODEL_CACHE["explainer"], _MODEL_CACHE["features"]


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
            "model_ready": os.path.exists(MODEL_PATH),
        }
    )


# ---------------------------------------------------------------------------
#  Personal prediction endpoint — receives the user's own measurements and
#  returns risk + SHAP attribution computed by the same XGBoost model the
#  engine uses on the streaming demo.
# ---------------------------------------------------------------------------
class PredictRequest(BaseModel):
    male: int = Field(..., ge=0, le=1, description="1 = hombre, 0 = mujer")
    age: int = Field(..., ge=18, le=110)
    education: int = Field(2, ge=1, le=4)
    currentSmoker: int = Field(0, ge=0, le=1)
    cigsPerDay: float = Field(0, ge=0, le=80)
    BPMeds: int = Field(0, ge=0, le=1)
    prevalentStroke: int = Field(0, ge=0, le=1)
    prevalentHyp: int = Field(0, ge=0, le=1)
    diabetes: int = Field(0, ge=0, le=1)
    totChol: float = Field(..., ge=80, le=600)
    sysBP: float = Field(..., ge=60, le=260)
    diaBP: float = Field(..., ge=30, le=160)
    BMI: float = Field(..., ge=10, le=70)
    heartRate: float = Field(..., ge=30, le=220)
    glucose: float = Field(..., ge=30, le=500)


@app.post("/api/predict")
def predict(req: PredictRequest):
    model, explainer, features = _ensure_model()

    payload = req.model_dump()
    df = pd.DataFrame([payload])
    if features:
        df = df.reindex(columns=features)

    prediction = int(model.predict(df)[0])
    probability = float(model.predict_proba(df)[0][1])

    shap_vals = explainer.shap_values(df)
    if isinstance(shap_vals, list):
        sv = shap_vals[1][0]
    else:
        sv = shap_vals[0]

    fi = pd.DataFrame({"feature": df.columns, "importance": sv})
    fi["abs"] = fi["importance"].abs()
    top = fi.sort_values("abs", ascending=False).head(5)
    shap_top = [
        {"name": str(row["feature"]), "impact": float(row["importance"])}
        for _, row in top.iterrows()
    ]

    try:
        with open("/data/custom_patient.json", "w") as f:
            json.dump(payload, f)
    except Exception as e:
        print(f"Failed to save custom patient: {e}")

    return {
        "prediction": prediction,
        "risk_pct": probability * 100,
        "shap": shap_top,
        "input_echo": payload,
    }


@app.get("/")
def root():
    return FileResponse(INDEX_PATH)
