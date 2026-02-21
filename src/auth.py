import streamlit as st
import psycopg2
from src.database import get_db_connection
from src.utils import hash_password, check_password, validate_password, validate_phone

def check_username_availability(username):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count == 0
    except Exception as e:
        st.error(f"Error checking username: {e}")
        return False

def check_phone_availability(phone):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE phone_number = %s", (phone,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count == 0
    except Exception as e:
        st.error(f"Error checking phone: {e}")
        return False

def check_email_availability(email):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE email = %s", (email,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count == 0
    except Exception as e:
        st.error(f"Error checking email: {e}")
        return False

def add_staff_member(username, email, phone, role, temp_password):
    # Checks
    if not check_username_availability(username):
        return False, "Username already taken."
    if not check_phone_availability(phone):
        return False, "Phone number already registered."
    if email and not check_email_availability(email):
        return False, "Email already registered."
        
    hashed_pw = hash_password(temp_password)
    
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed."
        
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, email, phone_number, role, password_hash, must_change_password)
            VALUES (%s, %s, %s, %s, %s, TRUE)
        """, (username, email, phone, role, hashed_pw))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Staff added successfully."
    except Exception as e:
        return False, f"Error adding staff: {e}"


def get_user_profile(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT username, email, phone_number FROM users WHERE user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return None
        return {
            "username": row[0],
            "email": row[1],
            "phone_number": row[2],
        }
    except Exception:
        return None


def update_user_profile(user_id, email, phone):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed."

    email = email.strip() if email else None
    phone = phone.strip() if phone else None

    if not phone:
        return False, "Phone number is required."
    if not phone.isdigit() or len(phone) != 10:
        return False, "Phone number must be exactly 10 digits."

    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT email, phone_number FROM users WHERE user_id = %s",
            (user_id,),
        )
        current = cur.fetchone()
        if not current:
            cur.close()
            conn.close()
            return False, "User not found."

        current_email, current_phone = current

        if phone != current_phone:
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE phone_number = %s AND user_id <> %s",
                (phone, user_id),
            )
            if cur.fetchone()[0] > 0:
                cur.close()
                conn.close()
                return False, "Phone number already registered."

        if email and email != current_email:
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE email = %s AND user_id <> %s",
                (email, user_id),
            )
            if cur.fetchone()[0] > 0:
                cur.close()
                conn.close()
                return False, "Email already registered."

        cur.execute(
            """
            UPDATE users
            SET email = %s, phone_number = %s
            WHERE user_id = %s
            """,
            (email, phone, user_id),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, "Profile updated successfully."
    except Exception as e:
        return False, f"Error updating profile: {e}"

def update_password(user_id, new_password):
    hashed_pw = hash_password(new_password)
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed."
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE users 
            SET password_hash = %s, must_change_password = FALSE 
            WHERE user_id = %s
        """, (hashed_pw, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Password updated successfully."
    except Exception as e:
        return False, f"Error updating password: {e}"

def register_user(username, password, phone, role):
    if not check_username_availability(username):
        return False, "Username already taken."
    if not check_phone_availability(phone):
        return False, "Phone number already registered."
    
    hashed_pw = hash_password(password)
    
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed."
        
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, password_hash, phone_number, role)
            VALUES (%s, %s, %s, %s)
        """, (username, hashed_pw, phone, role))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Registration successful! Please login."
    except Exception as e:
        return False, f"Registration failed: {e}"

def login_user(username, password):
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed."
        
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, password_hash, role, is_active, must_change_password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            # Check is_active status
            if not user[4]: # is_active is at index 4
                return None, "Account is deactivated. Please contact admin."

            if check_password(password, user[2]):
                return {
                    "user_id": user[0],
                    "username": user[1],
                    "role": user[3],
                    "must_change_password": user[5] if user[5] is not None else False
                }, "Login successful"
        
        return None, "Invalid username or password"
    except Exception as e:
        return None, f"Login error: {e}"
