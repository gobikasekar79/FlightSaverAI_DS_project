"""
ml_utils.py
Shared machine-learning utilities for FlightSaver AI.

Handles:
  - Loading trained models (rf_price_model.pkl, xgb_delay_model.pkl) and their
    LabelEncoders, with safe fallbacks if files are missing or corrupted.
  - Encoding raw user input into model-ready feature vectors.
  - Rule-based heuristic engines that guarantee the app NEVER crashes even
    when no trained model is present.
"""

from pathlib import Path
import joblib
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# This file lives at <PROJECT_ROOT>/app/utils/ml_utils.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = PROJECT_ROOT / "models"

PRICE_MODEL_PATH = MODEL_DIR / "rf_price_model.pkl"
PRICE_ENCODERS_PATH = MODEL_DIR / "encoders.pkl"
DELAY_MODEL_PATH = MODEL_DIR / "xgb_delay_model.pkl"
DELAY_ENCODERS_PATH = MODEL_DIR / "delay_encoders.pkl"

# ---------------------------------------------------------------------------
# Feature contracts (MUST stay aligned with train_models.py)
# ---------------------------------------------------------------------------
PRICE_FEATURES = [
    "airline", "source_city", "destination_city",
    "departure_time", "class", "days_left", "duration",
]
DELAY_FEATURES = [
    "airline", "source_city", "destination_city",
    "departure_time", "stops",
]
NUMERIC_FEATURES = {"days_left", "duration"}

# ---------------------------------------------------------------------------
# Heuristic reference tables (used when trained models are unavailable)
# ---------------------------------------------------------------------------
AIRLINE_BASE_FARE = {
    "IndiGo": 4500, "Air India": 5800, "SpiceJet": 4200,
    "Vistara": 6200, "GoAir": 4300, "AirAsia": 4100,
}
AIRLINE_DELAY_BIAS = {
    "IndiGo": 0.12, "Air India": 0.28, "SpiceJet": 0.22,
    "Vistara": 0.10, "GoAir": 0.20, "AirAsia": 0.18,
}
DEPARTURE_TIME_PRICE_MULT = {
    "Early_Morning": 0.95, "Morning": 1.05, "Afternoon": 1.0,
    "Evening": 1.1, "Night": 0.98, "Late_Night": 0.9,
}
DEPARTURE_TIME_DELAY_MULT = {
    "Early_Morning": 0.8, "Morning": 0.9, "Afternoon": 1.05,
    "Evening": 1.3, "Night": 1.1, "Late_Night": 0.95,
}
STOPS_DELAY_MULT = {"zero": 0.8, "one": 1.15, "two_or_more": 1.4}

# ---------------------------------------------------------------------------
# Model / encoder caching (Streamlit reruns the script on every interaction,
# so we cache in-process to avoid re-reading disk on every widget change).
# ---------------------------------------------------------------------------
_cache = {}


def _safe_load(path: Path):
    """Load a joblib artifact; return None on any failure instead of raising."""
    if not path.exists():
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


def load_price_pipeline():
    if "price_model" not in _cache:
        _cache["price_model"] = _safe_load(PRICE_MODEL_PATH)
        _cache["price_encoders"] = _safe_load(PRICE_ENCODERS_PATH)
    return _cache["price_model"], _cache["price_encoders"]


def load_delay_pipeline():
    if "delay_model" not in _cache:
        _cache["delay_model"] = _safe_load(DELAY_MODEL_PATH)
        _cache["delay_encoders"] = _safe_load(DELAY_ENCODERS_PATH)
    return _cache["delay_model"], _cache["delay_encoders"]


def models_available():
    """Return dict describing which trained models were successfully loaded."""
    price_model, price_enc = load_price_pipeline()
    delay_model, delay_enc = load_delay_pipeline()
    return {
        "price_model": price_model is not None and price_enc is not None,
        "delay_model": delay_model is not None and delay_enc is not None,
    }


def _encode_row(row_dict, encoders, feature_order):
    """Turn a dict of raw inputs into a numeric feature vector using the
    trained LabelEncoders. Unseen categories fall back to a stable hash
    bucket instead of raising, so a live app never crashes on new values."""
    encoded = []
    for feat in feature_order:
        val = row_dict[feat]
        if feat in NUMERIC_FEATURES:
            encoded.append(val)
            continue
        enc = encoders.get(feat) if encoders else None
        if enc is not None and val in getattr(enc, "classes_", []):
            encoded.append(int(enc.transform([val])[0]))
        else:
            # Unseen category or missing encoder -> stable fallback bucket
            encoded.append(abs(hash(val)) % 1000)
    return encoded


# ---------------------------------------------------------------------------
# Heuristic engines (fallback logic - zero external dependencies)
# ---------------------------------------------------------------------------
def heuristic_price(inputs: dict) -> float:
    base = AIRLINE_BASE_FARE.get(inputs["airline"], 4500)
    class_mult = 3.2 if inputs.get("class") == "Business" else 1.0
    duration_add = inputs.get("duration", 2.0) * 350

    days_left = inputs.get("days_left", 15)
    if days_left <= 2:
        urgency_mult = 1.55
    elif days_left <= 7:
        urgency_mult = 1.25
    elif days_left <= 20:
        urgency_mult = 1.05
    else:
        urgency_mult = 0.92

    time_mult = DEPARTURE_TIME_PRICE_MULT.get(inputs.get("departure_time"), 1.0)
    price = (base + duration_add) * class_mult * urgency_mult * time_mult

    # Small deterministic route-based variation so different city pairs differ
    route_key = (inputs.get("source_city", ""), inputs.get("destination_city", ""))
    noise = abs(hash(route_key)) % 400
    return max(1500.0, price + noise)


def heuristic_delay_risk(inputs: dict) -> float:
    bias = AIRLINE_DELAY_BIAS.get(inputs["airline"], 0.18)
    stops_mult = STOPS_DELAY_MULT.get(inputs.get("stops", "zero"), 1.0)
    time_mult = DEPARTURE_TIME_DELAY_MULT.get(inputs.get("departure_time"), 1.0)
    risk = bias * stops_mult * time_mult * 100
    return min(95.0, max(2.0, risk))


# ---------------------------------------------------------------------------
# Public prediction API used by dashboard.py, charts.py, alerts.py
# ---------------------------------------------------------------------------
def predict_price(inputs: dict) -> float:
    model, encoders = load_price_pipeline()
    if model is not None and encoders is not None:
        try:
            row = _encode_row(inputs, encoders, PRICE_FEATURES)
            return float(model.predict(pd.DataFrame([row], columns=PRICE_FEATURES))[0])
        except Exception:
            pass  # fall through to heuristic
    return heuristic_price(inputs)


def predict_delay_risk(inputs: dict) -> float:
    """Returns delay risk as a percentage (0-100)."""
    model, encoders = load_delay_pipeline()
    if model is not None and encoders is not None:
        try:
            row = _encode_row(inputs, encoders, DELAY_FEATURES)
            proba = model.predict_proba(pd.DataFrame([row], columns=DELAY_FEATURES))[0]
            risk = proba[1] if len(proba) > 1 else proba[0]
            return float(risk * 100)
        except Exception:
            pass  # fall through to heuristic
    return heuristic_delay_risk(inputs)
