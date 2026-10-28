"""
metrices.py
Renders the top-of-dashboard KPI summary cards.
"""

import streamlit as st


def render_kpi_cards(predicted_price: float, delay_risk: float,
                      best_day: int | None = None, price_trend: float | None = None) -> None:
    """Render four KPI metric cards: predicted fare, delay risk, best booking
    day, and short-term price trend."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="💰 Predicted Fare", value=f"₹{predicted_price:,.0f}")

    with col2:
        risk_label = "Low" if delay_risk < 33 else "Moderate" if delay_risk < 66 else "High"
        st.metric(
            label="⏱️ Delay Risk",
            value=f"{delay_risk:.1f}%",
            delta=risk_label,
            delta_color="inverse",
        )

    with col3:
        if best_day is not None:
            st.metric(label="📅 Best Day to Book", value=f"{best_day} days left")
        else:
            st.metric(label="📅 Best Day to Book", value="N/A")

    with col4:
        if price_trend is not None:
            arrow = "📈" if price_trend > 0 else "📉" if price_trend < 0 else "➖"
            st.metric(label="7-Day Trend", value=f"{arrow} {abs(price_trend):.1f}%")
        else:
            st.metric(label="7-Day Trend", value="N/A")
