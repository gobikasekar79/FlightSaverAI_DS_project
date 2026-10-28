"""
charts.py
Dynamic Plotly visualizations for FlightSaver AI:
  - price_projection_chart: fare trajectory across days-left-to-departure (50 -> 0)
  - reliability_benchmark_chart: delay-risk comparison across all competitor airlines
"""

import pandas as pd
import plotly.graph_objects as go

from utils.ml_utils import predict_price, predict_delay_risk, AIRLINE_BASE_FARE


def price_projection_chart(inputs: dict):
    """Recompute the estimated fare for every lead time from 50 days out
    down to 0 (departure day), holding airline/route/class/duration fixed,
    and return a Plotly dark-themed line chart plus the row with the
    lowest predicted price."""
    days_range = list(range(50, -1, -1))
    prices = []
    for d in days_range:
        row = dict(inputs)
        row["days_left"] = d
        prices.append(predict_price(row))

    df = pd.DataFrame({"days_left": days_range, "price": prices})
    best_row = df.loc[df["price"].idxmin()]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["days_left"], y=df["price"],
        mode="lines+markers", name="Projected Fare",
        line=dict(color="#00CC96", width=3), marker=dict(size=5),
        hovertemplate="Days left: %{x}<br>Fare: ₹%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[best_row["days_left"]], y=[best_row["price"]],
        mode="markers", name="Best Price",
        marker=dict(color="#FFD700", size=14, symbol="star"),
        hovertemplate="Best day: %{x} days left<br>Fare: ₹%{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        title=f"Price Projection: {inputs['source_city']} → {inputs['destination_city']} ({inputs['airline']})",
        xaxis_title="Days Left Until Departure",
        yaxis_title="Estimated Fare (₹)",
        template="plotly_dark",
        xaxis=dict(autorange="reversed"),
        hovermode="x unified",
        height=440,
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig, best_row


def reliability_benchmark_chart(inputs: dict):
    """Compute relative delay-risk percentages across every competitor
    airline for the currently selected route/time/stops, and return a
    horizontal bar chart plus the underlying dataframe."""
    airlines = list(AIRLINE_BASE_FARE.keys())
    risks = []
    for airline in airlines:
        row = dict(inputs)
        row["airline"] = airline
        risks.append(predict_delay_risk(row))

    df = pd.DataFrame({"airline": airlines, "delay_risk": risks}).sort_values("delay_risk")
    colors = ["#00CC96" if r < 20 else "#FFA15A" if r < 40 else "#EF553B" for r in df["delay_risk"]]

    fig = go.Figure(go.Bar(
        x=df["delay_risk"], y=df["airline"], orientation="h",
        marker_color=colors,
        text=[f"{r:.1f}%" for r in df["delay_risk"]],
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        title=f"Airline Reliability Benchmark: {inputs['source_city']} → {inputs['destination_city']}",
        xaxis_title="Delay Risk (%)",
        yaxis_title="Airline",
        template="plotly_dark",
        height=400,
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig, df
