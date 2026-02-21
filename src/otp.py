import streamlit as st
import random
from datetime import datetime, timedelta

def generate_otp():
    """Generate a 6-digit OTP with 5-minute expiration."""
    otp = random.randint(100000, 999999)
    otp_expiry = datetime.now() + timedelta(minutes=5)
    return otp, otp_expiry

def validate_otp(user_otp, actual_otp, expiry):
    """Validate the provided OTP against the generated one."""
    if not actual_otp or not expiry:
        return False
    
    if datetime.now() > expiry:
        return False
    
    try:
        return int(user_otp) == int(actual_otp)
    except:
        return False
