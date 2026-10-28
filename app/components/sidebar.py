"""
sidebar.py
Universal flight input parameter widgets, shared across all authenticated pages.
"""

import streamlit as st

AIRLINES = ["IndiGo", "Air India", "SpiceJet", "Vistara", "GoAir", "AirAsia"]
CITIES = ["Delhi", "Mumbai", "Bangalore", "Kolkata", "Hyderabad", "Chennai"]
DEPARTURE_TIMES = ["Early_Morning", "Morning", "Afternoon", "Evening", "Night", "Late_Night"]
CLASSES = ["Economy", "Business"]
STOPS = ["zero", "one", "two_or_more"]


def get_sidebar_inputs() -> dict:
    """Render the shared flight-search widgets in the sidebar and return the
    current selections as a plain dict, ready to feed into the ML pipelines."""
    st.sidebar.header("✈️ Flight Parameters")

    airline = st.sidebar.selectbox("Airline", AIRLINES, key="sb_airline")
    source_city = st.sidebar.selectbox("Source City", CITIES, index=0, key="sb_source")

    dest_options = [c for c in CITIES if c != source_city]
    destination_city = st.sidebar.selectbox("Destination City", dest_options, index=0, key="sb_dest")

    departure_time = st.sidebar.selectbox("Departure Time", DEPARTURE_TIMES, key="sb_dep_time")
    flight_class = st.sidebar.selectbox("Class", CLASSES, key="sb_class")
    stops = st.sidebar.selectbox("Stops", STOPS, key="sb_stops")

    days_left = st.sidebar.slider(
        "Days Left Until Departure", min_value=0, max_value=50, value=15, key="sb_days_left"
    )
    duration = st.sidebar.slider(
        "Flight Duration (hours)", min_value=0.5, max_value=15.0, value=2.5, step=0.5, key="sb_duration"
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("FlightSaver AI © 2026")

    return {
        "airline": airline,
        "source_city": source_city,
        "destination_city": destination_city,
        "departure_time": departure_time,
        "class": flight_class,
        "stops": stops,
        "days_left": days_left,
        "duration": float(duration),
    }
