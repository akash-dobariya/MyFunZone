import streamlit as st
import time
from src.database import init_db
from src.auth import login_user, register_user, check_username_availability, update_password
from src.utils import validate_password, validate_phone, apply_role_style
from src.otp import generate_otp, validate_otp
from src.session import init_session, login_user_session, get_current_user, logout_user_session
from views.admin import show_admin_dashboard
from views.staff import show_staff_dashboard
from views.user import show_user_dashboard

# Page Config
st.set_page_config(page_title="MyFunZone", layout="centered")

# Initialize Session State
init_session()

def show_change_password():
    st.title("Change Password")
    st.warning("You must change your password before continuing.")
    
    with st.form("change_password_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Update Password")
        
        if submitted:
            if new_password != confirm_password:
                st.error("Passwords do not match.")
            elif not validate_password(new_password):
                 st.error("Password does not meet complexity requirements.")
            else:
                current_user = get_current_user()
                success, msg = update_password(current_user['user_id'], new_password)
                if success:
                    st.success("Password updated successfully! Please login again with your new password.")
                    logout_user_session() 
                    st.session_state['user']['must_change_password'] = False
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)

def show_login():
    st.title("Login to MyFunZone")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                user, message = login_user(username, password)
                if user:
                    st.success(message)
                    login_user_session(user)
                    st.rerun()
                else:
                    st.error(message)
    
    st.markdown("---")
    st.write("Didn't have an account?")
    if st.button("Signup"):
        st.session_state.page = 'signup'
        st.rerun()

def show_signup():
    st.title("Signup for MyFunZone")
    
    # Username with real-time availability check
    username = st.text_input("Username", key="signup_username")
    if username:
        if check_username_availability(username):
            st.success("Username available!")
        else:
            st.error("Username taken.")

    password = st.text_input("Password", type="password")
    re_password = st.text_input("Re-Enter Password", type="password")
    
    # Password validation helper
    if password:
        if validate_password(password):
            st.caption("✅ Password strength good.")
        else:
            st.caption("❌ Password must be >6 chars, with number, letter, and special char.")
            
    phone = st.text_input("Phone Number", placeholder="Enter 10-digit phone number", max_chars=10)
    
    # Real-time phone validation
    phone_valid = False
    if phone:
        if phone.isdigit() and len(phone) == 10:
            st.caption("✅ Phone number is valid.")
            phone_valid = True
        else:
            st.caption("❌ Please enter exactly 10 digits.")
    
    if st.button("Register"):
        # Validation
        if not username:
            st.error("Username is required.")
        elif not check_username_availability(username):
            st.error("Username is already taken.")
        elif not password or not re_password:
            st.error("Password fields are required.")
        elif password != re_password:
            st.error("Passwords do not match.")
        elif not validate_password(password):
            st.error("Password does not meet complexity requirements.")
        elif not phone:
            st.error("Phone number is required.")
        elif not phone_valid:
             st.error("Invalid phone number format. Must be 10 digits.")
        else:
            # Store data and move to OTP verification
            role = 'user' 
            
            # Generate and Send OTP
            otp, otp_expiry = generate_otp()
            st.session_state.otp = otp
            st.session_state.otp_expiry = otp_expiry
            st.session_state.signup_data = (username, password, phone, role)
            
            # Simulate sending OTP
            st.warning(f"🔐 INBUILT OTP SERVICE : **{otp}**")
            
            # Brief pause to let user see the message
            time.sleep(1)
            st.session_state.page = 'verify_otp'
            st.rerun()

    if st.button("Back to Login"):
        st.session_state.page = 'login'
        st.rerun()

def show_verify_otp():
    st.title("Verify OTP")
    
    # Always display OTP in Inbuilt Mode
    if st.session_state.otp:
        st.warning(f"🔐 INBUILT OTP SERVICE : **{st.session_state.otp}**")

    otp_input = st.text_input("Enter OTP", type="password")
    
    if st.button("Verify"):
        if not otp_input:
            st.error("Please enter OTP.")
        else:
            if validate_otp(otp_input, st.session_state.otp, st.session_state.otp_expiry):
                # OTP Verified, proceed to register
                username, password, phone, role = st.session_state.signup_data
                success, message = register_user(username, password, phone, role)
                
                if success:
                    st.success(message)
                    # Clear sensitive data
                    st.session_state.signup_data = None
                    st.session_state.otp = None
                    st.session_state.otp_expiry = None
                    
                    time.sleep(2)
                    st.session_state.page = 'login'
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Invalid or expired OTP. Please try again.")
                
    if st.button("Resend OTP"):
        if st.session_state.signup_data:
            username, password, phone, role = st.session_state.signup_data
            otp, otp_expiry = generate_otp()
            st.session_state.otp = otp
            st.session_state.otp_expiry = otp_expiry
            st.warning(f"OTP generated : {otp}")
        else:
            st.error("Session expired. Please sign up again.")
            st.session_state.page = 'signup'
            st.rerun()

    st.markdown("---")
    if st.button("Back to Signup"):
        st.session_state.page = 'signup'
        st.rerun()

def main():
    # Initialize Database
    init_db()
    
    current_user = get_current_user()

    if current_user:
        # Check for forced password reset
        if current_user.get('must_change_password'):
            show_change_password()
        else:
            # User is logged in, show role-specific dashboard
            role = current_user['role']
            apply_role_style(role)
            
            if role == 'admin':
                show_admin_dashboard()
            elif role == 'staff':
                show_staff_dashboard()
            elif role == 'user':
                show_user_dashboard()
            else:
                st.error("Unknown role.")
    else:
        # Not logged in
        apply_role_style(None) # Apply default style
        
        if st.session_state.page == 'login':
            show_login()
        elif st.session_state.page == 'signup':
            show_signup()
        elif st.session_state.page == 'verify_otp':
            show_verify_otp()

if __name__ == "__main__":
    main()
