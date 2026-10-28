"""
app.py
Main entry point for FlightSaver AI.

Run from the project root with:
    streamlit run app/app.py
"""

import sys
import os

# Add this "app" folder to sys.path so imports like
# `from components.sidebar import ...` resolve correctly.
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

import streamlit as st

st.set_page_config(
    page_title="FlightSaver AI",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from components.sidebar import get_sidebar_inputs
from pages import login, dashboard, alerts, profile

# ---------------------------------------------------------------------------
# Dark theme polish
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .stApp { background-color: #0e1117; }
        section[data-testid="stSidebar"] { background-color: #161a23; }
        div[data-testid="stMetric"] {
            background-color: #1a1f2b;
            border: 1px solid #2a2f3b;
            border-radius: 10px;
            padding: 14px 16px;
        }
        div[data-testid="stMetricLabel"] { color: #9aa4b2; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

NAV_PAGES = ["Dashboard", "Alerts", "Profile"]


def init_session_state() -> None:
    defaults = {"logged_in": False, "user": None, "page": "Dashboard"}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main() -> None:
    init_session_state()

    # --- Unauthenticated: show login/signup only ---
    if not st.session_state.logged_in:
        login.render_login_page()
        return

    # --- Authenticated: full app shell ---
    st.sidebar.title("✈️ FlightSaver AI")
    st.sidebar.write(f"Welcome, **{st.session_state.user['full_name']}**")

    current_index = NAV_PAGES.index(st.session_state.page) if st.session_state.page in NAV_PAGES else 0
    nav = st.sidebar.radio("Navigate", NAV_PAGES, index=current_index, key="nav_radio")
    st.session_state.page = nav
    st.sidebar.markdown("---")

    inputs = get_sidebar_inputs()

    if nav == "Dashboard":
        dashboard.render_dashboard(inputs)
    elif nav == "Alerts":
        alerts.render_alerts_page(inputs)
    elif nav == "Profile":
        profile.render_profile_page()


main()