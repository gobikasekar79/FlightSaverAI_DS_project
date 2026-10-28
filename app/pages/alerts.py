"""
alerts.py
Custom threshold-based alerting: users can define a fare-drop and/or
delay-risk threshold per route/airline, persisted to data/alerts.json
and evaluated live against current predictions.
"""

import json
from pathlib import Path
from datetime import datetime

import streamlit as st

from utils.ml_utils import predict_price, predict_delay_risk

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALERTS_DB_PATH = PROJECT_ROOT / "data" / "alerts.json"


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------
def _ensure_db() -> None:
    ALERTS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not ALERTS_DB_PATH.exists():
        ALERTS_DB_PATH.write_text(json.dumps({}, indent=2))


def load_alerts() -> dict:
    _ensure_db()
    try:
        with open(ALERTS_DB_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_alerts(alerts: dict) -> None:
    _ensure_db()
    with open(ALERTS_DB_PATH, "w") as f:
        json.dump(alerts, f, indent=2)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
def render_alerts_page(inputs: dict) -> None:
    if not st.session_state.get("logged_in"):
        st.warning("Please log in to view alerts.")
        st.stop()

    st.title("🔔 Fare & Delay Alerts")
    user_email = st.session_state.user["email"]

    all_alerts = load_alerts()
    user_alerts = all_alerts.get(user_email, [])

    st.subheader("Create a New Alert")
    st.caption(
        f"For your currently selected route: "
        f"**{inputs['source_city']} → {inputs['destination_city']}** on **{inputs['airline']}**"
    )
    with st.form("alert_form"):
        c1, c2 = st.columns(2)
        with c1:
            price_threshold = st.number_input(
                "Notify me if fare drops below (₹)", min_value=0, value=5000, step=100
            )
        with c2:
            delay_threshold = st.slider("Notify me if delay risk exceeds (%)", 0, 100, 30)
        submitted = st.form_submit_button("Create Alert", width="stretch")

    if submitted:
        new_alert = {
            "route": f"{inputs['source_city']} → {inputs['destination_city']}",
            "airline": inputs["airline"],
            "price_threshold": price_threshold,
            "delay_threshold": delay_threshold,
            "created_at": datetime.now().isoformat(),
        }
        user_alerts.append(new_alert)
        all_alerts[user_email] = user_alerts
        save_alerts(all_alerts)
        st.success("Alert created!")
        st.rerun()

    st.markdown("---")
    st.subheader("Your Active Alerts")

    if not user_alerts:
        st.info("You have no active alerts yet. Create one above.")
        return

    current_price = predict_price(inputs)
    current_delay = predict_delay_risk(inputs)

    for idx, alert in enumerate(user_alerts):
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.markdown(f"**{alert['route']}** · {alert['airline']}")
                st.caption(
                    f"Alert if fare < ₹{alert['price_threshold']:,} "
                    f"or delay risk > {alert['delay_threshold']}%"
                )
            with c2:
                same_route = (
                    alert["route"] == f"{inputs['source_city']} → {inputs['destination_city']}"
                    and alert["airline"] == inputs["airline"]
                )
                price_hit = same_route and current_price < alert["price_threshold"]
                delay_hit = same_route and current_delay > alert["delay_threshold"]

                if price_hit:
                    st.success(f"💰 Fare alert triggered: ₹{current_price:,.0f}")
                if delay_hit:
                    st.error(f"⏱️ Delay risk alert triggered: {current_delay:.1f}%")
                if not price_hit and not delay_hit:
                    st.caption(
                        "Matches current selection - no trigger yet."
                        if same_route else "Select this route/airline to evaluate live."
                    )
            with c3:
                if st.button("Delete", key=f"del_alert_{idx}"):
                    user_alerts.pop(idx)
                    all_alerts[user_email] = user_alerts
                    save_alerts(all_alerts)
                    st.rerun()
