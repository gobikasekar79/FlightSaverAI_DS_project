"""
dashboard.py
Main prediction dashboard: KPI summary, price projection curve, and
airline reliability benchmark. Route-protected - requires an authenticated
session.
"""

import streamlit as st

from components.charts import price_projection_chart, reliability_benchmark_chart
from components.metrices import render_kpi_cards
from utils.ml_utils import predict_price, predict_delay_risk, models_available


def render_dashboard(inputs: dict) -> None:
    # ---- Route protection ----
    if not st.session_state.get("logged_in"):
        st.warning("Please log in to view the dashboard.")
        st.stop()

    st.title("📊 Fare & Delay Prediction Dashboard")
    st.caption(
        f"{inputs['source_city']} → {inputs['destination_city']} · "
        f"{inputs['airline']} · {inputs['class']} · {inputs['stops'].replace('_', ' ')} stop(s)"
    )

    status = models_available()
    if not status["price_model"] or not status["delay_model"]:
        st.info(
            "ℹ️ Running on the built-in heuristic engine because one or more trained "
            "model files were not found in `models/`. Run `train_models.py` to enable "
            "full ML predictions. The app remains fully functional either way.",
            icon="ℹ️",
        )

    # ---- Core predictions for the currently selected inputs ----
    predicted_price = predict_price(inputs)
    delay_risk = predict_delay_risk(inputs)

    # ---- Price projection curve (also gives us the cheapest booking day) ----
    price_fig, best_row = price_projection_chart(inputs)

    # ---- 7-day forward trend, for the KPI card ----
    price_trend = None
    try:
        future_days = min(50, inputs["days_left"] + 7)
        future_inputs = dict(inputs)
        future_inputs["days_left"] = future_days
        future_price = predict_price(future_inputs)
        if future_price:
            price_trend = ((predicted_price - future_price) / future_price) * 100
    except Exception:
        price_trend = None

    render_kpi_cards(
        predicted_price,
        delay_risk,
        best_day=int(best_row["days_left"]),
        price_trend=price_trend,
    )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(price_fig, width="stretch")
    with col2:
        reliability_fig, _ = reliability_benchmark_chart(inputs)
        st.plotly_chart(reliability_fig, width="stretch")

    st.markdown("---")
    with st.expander("ℹ️ How these predictions work"):
        st.write(
            "Fare predictions use a trained Random Forest Regressor when a model "
            "file is available in `models/rf_price_model.pkl`, falling back to a "
            "transparent rule-based heuristic engine (base fare, class multiplier, "
            "booking-urgency curve, and time-of-day adjustment) when it isn't.\n\n"
            "Delay risk uses an XGBoost classifier's `predict_proba()` output when "
            "`models/xgb_delay_model.pkl` is available, or a heuristic based on "
            "airline history, number of stops, and departure time window otherwise."
        )
