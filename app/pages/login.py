"""
login.py
Authentication page: user registration & login, backed by a local JSON
"database" at data/users.json. Passwords are stored as SHA-256 hashes
(never in plaintext).
"""

import json
import hashlib
import re
from pathlib import Path
from datetime import datetime

import streamlit as st

# This file lives at <PROJECT_ROOT>/app/pages/login.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
USERS_DB_PATH = PROJECT_ROOT / "data" / "users.json"


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------
def _ensure_db() -> None:
    USERS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not USERS_DB_PATH.exists():
        USERS_DB_PATH.write_text(json.dumps({}, indent=2))


def load_users() -> dict:
    _ensure_db()
    try:
        with open(USERS_DB_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_users(users: dict) -> None:
    _ensure_db()
    with open(USERS_DB_PATH, "w") as f:
        json.dump(users, f, indent=2)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_valid_email(email: str) -> bool:
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) is not None


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
def render_login_page() -> None:
    st.markdown("<h1 style='text-align:center;'>✈️ FlightSaver AI</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:gray;'>Predictive fares. Smarter bookings.</p>",
        unsafe_allow_html=True,
    )
    st.write("")

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        tab_login, tab_signup = st.tabs(["🔐 Login", "📝 Sign Up"])

        # ------------------------------------------------------------- Login
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Login", width="stretch")

            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    users = load_users()
                    user = users.get(email.strip().lower())
                    if user and user["password"] == hash_password(password):
                        st.session_state.logged_in = True
                        st.session_state.user = {
                            "email": email.strip().lower(),
                            "full_name": user["full_name"],
                        }
                        st.session_state.page = "Dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

        # ------------------------------------------------------------ Signup
        with tab_signup:
            with st.form("signup_form"):
                full_name = st.text_input("Full Name", key="signup_name")
                email_s = st.text_input("Email", key="signup_email")
                password_s = st.text_input("Password", type="password", key="signup_password")
                password_confirm = st.text_input(
                    "Confirm Password", type="password", key="signup_confirm"
                )
                submitted_s = st.form_submit_button("Create Account", width="stretch")

            if submitted_s:
                if not full_name or not email_s or not password_s:
                    st.error("Please fill in all fields.")
                elif not is_valid_email(email_s):
                    st.error("Please enter a valid email address.")
                elif len(password_s) < 6:
                    st.error("Password must be at least 6 characters.")
                elif password_s != password_confirm:
                    st.error("Passwords do not match.")
                else:
                    users = load_users()
                    key = email_s.strip().lower()
                    if key in users:
                        st.error("An account with this email already exists.")
                    else:
                        users[key] = {
                            "full_name": full_name.strip(),
                            "password": hash_password(password_s),
                            "created_at": datetime.now().isoformat(),
                        }
                        save_users(users)
                        st.success("Account created successfully! Please log in from the Login tab.")
