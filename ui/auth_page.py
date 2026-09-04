import time

import extra_streamlit_components as stx
import streamlit as st

from services.auth_service import register_user, verify_login


def get_cookie_manager():
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager()
    return st.session_state.cookie_manager


def _render_login_tab() -> None:
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        user = verify_login(email, password)
        if user:
            st.session_state.current_user = user
            cookie_manager = get_cookie_manager()
            cookie_manager.set("user_id", user["id"], key="set_login_cookie")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("Invalid email or password")


def _render_signup_tab() -> None:
    with st.form("signup_form"):
        email = st.text_input("Email", key="signup_email")
        display_name = st.text_input("Display name", key="signup_display_name")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input(
            "Confirm password", type="password", key="signup_confirm_password"
        )
        submitted = st.form_submit_button("Sign up")

    if submitted:
        if password != confirm_password:
            st.error("Passwords do not match.")
            return

        try:
            user = register_user(email, password, display_name)
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state.current_user = user
            cookie_manager = get_cookie_manager()
            cookie_manager.set("user_id", user["id"], key="set_login_cookie")
            time.sleep(0.5)
            st.rerun()


def render_auth_page() -> dict | None:
    st.title("AI Interview Intelligence Platform")

    login_tab, signup_tab = st.tabs(["Log in", "Sign up"])

    with login_tab:
        _render_login_tab()

    with signup_tab:
        _render_signup_tab()

    return st.session_state.get("current_user")
