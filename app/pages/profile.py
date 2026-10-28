"""
profile.py
User settings & account configuration: view account info, update full name,
change password, and log out.
"""

import streamlit as st

from pages.login import load_users, save_users, hash_password


def render_profile_page() -> None:
    if not st.session_state.get("logged_in"):
        st.warning("Please log in to view your profile.")
        st.stop()

    st.title("👤 Profile & Settings")

    user = st.session_state.user
    users = load_users()
    record = users.get(user["email"], {})

    st.subheader("Account Information")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Email", value=user["email"], disabled=True)
    with c2:
        member_since = record.get("created_at", "N/A")
        st.text_input("Member Since", value=member_since[:10] if member_since != "N/A" else "N/A", disabled=True)

    st.markdown("---")
    st.subheader("Update Profile")

    with st.form("update_profile"):
        new_name = st.text_input("Full Name", value=user["full_name"])
        st.markdown("**Change Password** _(leave blank to keep your current password)_")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Save Changes", width="stretch")

    if submitted:
        if new_password and new_password != confirm_password:
            st.error("New passwords do not match.")
        elif new_password and len(new_password) < 6:
            st.error("Password must be at least 6 characters.")
        elif not new_name.strip():
            st.error("Full name cannot be empty.")
        else:
            record["full_name"] = new_name.strip()
            if new_password:
                record["password"] = hash_password(new_password)
            users[user["email"]] = record
            save_users(users)
            st.session_state.user["full_name"] = new_name.strip()
            st.success("Profile updated successfully.")
            st.rerun()

    st.markdown("---")
    st.subheader("Session")
    if st.button("🚪 Log Out", width="stretch"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.page = "Dashboard"
        st.rerun()
