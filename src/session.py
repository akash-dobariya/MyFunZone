import streamlit as st

def init_session():
    """
    Initialize session state variables if they don't exist.
    
    """
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    if 'otp' not in st.session_state:
        st.session_state.otp = None
    if 'otp_expiry' not in st.session_state:
        st.session_state.otp_expiry = None
    if 'signup_data' not in st.session_state:
        st.session_state.signup_data = None

def login_user_session(user):
    """
    Log the user into the session.
    """
    st.session_state.user = user
    st.rerun()

def logout_user_session():
    """
    Log the user out of the session.
    Clears the user data and redirects to login.
    """
    st.session_state.user = None
    st.session_state.page = 'login'
    st.rerun()

def get_current_user():
    """
    Retrieve the current logged-in user.
    """
    return st.session_state.get('user')

def is_logged_in():
    """
    Check if a user is currently logged in.
    """
    return st.session_state.get('user') is not None
