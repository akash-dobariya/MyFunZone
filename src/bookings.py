from src.database import get_db_connection
import streamlit as st
import qrcode
from io import BytesIO
import base64
import uuid
from datetime import datetime, timedelta

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def cancel_booking(booking_id, user_role, user_id=None):
    """
    Cancel a booking based on role policies.
    Admin: Can cancel any booking.
    User: Can cancel own booking if start_time > 24 hours from now.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
        
    try:
        cur = conn.cursor()
        
        # Get booking details with slot info
        cur.execute("""
            SELECT b.user_id, b.status, s.slot_date, s.start_time
            FROM bookings b
            JOIN slots s ON b.slot_id = s.slot_id
            WHERE b.booking_id = %s
        """, (booking_id,))
        
        booking = cur.fetchone()
        if not booking:
            return False, "Booking not found"
            
        b_user_id, status, slot_date, start_time = booking
        
        if status == 'cancelled':
            return False, "Booking already cancelled"
            
        # Policy Check
        if user_role == 'user':
            if user_id and b_user_id != user_id:
                return False, "Unauthorized to cancel this booking"
                
            # Check time constraint (24 hours)
            slot_datetime = datetime.combine(slot_date, start_time)
            if slot_datetime < datetime.now() + timedelta(hours=24):
                return False, "Cancellation allowed only 24 hours before slot time"
                
        elif user_role != 'admin':
            return False, "Unauthorized role"
            
        # Update status
        cur.execute("UPDATE bookings SET status = 'cancelled' WHERE booking_id = %s", (booking_id,))
        
 
        cur.execute("UPDATE payments SET payment_status = 'refunded' WHERE booking_id = %s AND payment_status = 'paid'", (booking_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        return True, "Booking cancelled successfully"
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Error cancelling booking: {e}"

def reschedule_booking(booking_id, new_slot_id, user_role, user_id=None):
    """
    Reschedule booking to a new slot.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
        
    try:
        cur = conn.cursor()
        
        # Get current booking
        cur.execute("""
            SELECT b.user_id, b.status, b.number_of_players, s.price
            FROM bookings b
            JOIN slots s ON b.slot_id = s.slot_id
            WHERE b.booking_id = %s
        """, (booking_id,))
        
        booking = cur.fetchone()
        if not booking:
            return False, "Booking not found"
            
        b_user_id, status, num_players, old_price = booking
        
        if status != 'booked':
            return False, "Only active bookings can be rescheduled"
            
        if user_role == 'user' and user_id and b_user_id != user_id:
             return False, "Unauthorized"
             
        # Check new slot availability
        cur.execute("""
            SELECT s.max_players, s.price,
                   (s.max_players - COALESCE(SUM(b.number_of_players), 0)) as available_spots
            FROM slots s
            LEFT JOIN bookings b ON s.slot_id = b.slot_id AND b.status IN ('booked', 'checked_in')
            WHERE s.slot_id = %s
            GROUP BY s.slot_id
        """, (new_slot_id,))
        
        new_slot = cur.fetchone()
        if not new_slot:
            return False, "New slot not found"
            
        max_players, new_price, available_spots = new_slot
        
        if available_spots < num_players:
            return False, "Not enough spots in new slot"
            
     
        
        cur.execute("UPDATE bookings SET slot_id = %s WHERE booking_id = %s", (new_slot_id, booking_id))
        
        # Update payment amount if price changed?
        if new_price != old_price:
             new_total = new_price * num_players
             cur.execute("UPDATE payments SET amount = %s WHERE booking_id = %s", (new_total, booking_id))
        
        conn.commit()
        cur.close()
        conn.close()
        return True, "Booking rescheduled successfully"
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Error rescheduling: {e}"

def create_booking(user_id, slot_id, number_of_players):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cur = conn.cursor()
        
        # Verify slot availability again
        cur.execute("""
            SELECT s.max_players, s.price,
                   (s.max_players - COALESCE(SUM(b.number_of_players), 0)) as available_spots
            FROM slots s
            LEFT JOIN bookings b ON s.slot_id = b.slot_id AND b.status IN ('booked', 'checked_in')
            WHERE s.slot_id = %s
            GROUP BY s.slot_id
        """, (slot_id,))
        
        slot_data = cur.fetchone()
        if not slot_data:
            return False, "Slot not found"
            
        max_players, price, available_spots = slot_data
        
        if available_spots < number_of_players:
            return False, "Not enough spots available"
            
        # Generate unique QR code data
        unique_code = str(uuid.uuid4())
        qr_code_data = f"BOOKING:{unique_code}"
        
        # Create booking
        cur.execute("""
            INSERT INTO bookings (user_id, slot_id, number_of_players, qr_code, status)
            VALUES (%s, %s, %s, %s, 'booked')
            RETURNING booking_id
        """, (user_id, slot_id, number_of_players, qr_code_data))
        
        booking_id = cur.fetchone()[0]
        
        # Create payment record (pending)
        total_amount = price * number_of_players
        cur.execute("""
            INSERT INTO payments (booking_id, amount, payment_status, payment_method)
            VALUES (%s, %s, 'pending', 'online')
        """, (booking_id, total_amount))
        
        conn.commit()
        cur.close()
        conn.close()
        return True, booking_id
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Error creating booking: {e}"

def get_user_bookings(user_id):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT b.*, g.game_id as game_id, g.name as game_name, s.slot_date, s.start_time, s.end_time, p.amount, p.payment_status
            FROM bookings b
            JOIN slots s ON b.slot_id = s.slot_id
            JOIN games g ON s.game_id = g.game_id
            LEFT JOIN payments p ON b.booking_id = p.booking_id
            WHERE b.user_id = %s
            ORDER BY b.booking_time DESC
        """, (user_id,))
        
        bookings = []
        columns = [desc[0] for desc in cur.description]
        for row in cur.fetchall():
            bookings.append(dict(zip(columns, row)))
            
        cur.close()
        conn.close()
        return bookings
    except Exception as e:
        st.error(f"Error fetching bookings: {e}")
        return []

def get_all_bookings(start_date=None, end_date=None):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        query = """
            SELECT b.*, u.username, g.game_id as game_id, g.name as game_name, s.slot_date, s.start_time, s.end_time, p.amount, p.payment_status
            FROM bookings b
            JOIN users u ON b.user_id = u.user_id
            JOIN slots s ON b.slot_id = s.slot_id
            JOIN games g ON s.game_id = g.game_id
            LEFT JOIN payments p ON b.booking_id = p.booking_id
        """
        params = []
        
        if start_date and end_date:
            query += " WHERE s.slot_date BETWEEN %s AND %s"
            params.append(start_date)
            params.append(end_date)
        elif start_date:
             query += " WHERE s.slot_date = %s"
             params.append(start_date)
            
        query += " ORDER BY b.booking_time DESC"
        
        cur.execute(query, tuple(params))
        
        bookings = []
        columns = [desc[0] for desc in cur.description]
        for row in cur.fetchall():
            bookings.append(dict(zip(columns, row)))
            
        cur.close()
        conn.close()
        return bookings
    except Exception as e:
        st.error(f"Error fetching all bookings: {e}")
        return []

def get_revenue_stats(start_date=None, end_date=None):
    """
    Returns total revenue and revenue over time.
    """
    conn = get_db_connection()
    if not conn:
        return {'total_revenue': 0, 'daily_revenue': []}
        
    try:
        cur = conn.cursor()
        
        where_clause = " WHERE b.status IN ('booked', 'checked_in', 'completed') "
        params = []
        
        if start_date and end_date:
            where_clause += " AND s.slot_date BETWEEN %s AND %s"
            params.extend([start_date, end_date])
            
        # Total Revenue
        query_total = f"""
            SELECT COALESCE(SUM(p.amount), 0)
            FROM bookings b
            JOIN slots s ON b.slot_id = s.slot_id
            LEFT JOIN payments p ON b.booking_id = p.booking_id
            {where_clause}
        """
        cur.execute(query_total, tuple(params))
        total_revenue = cur.fetchone()[0]
        
        # Daily Revenue
        query_daily = f"""
            SELECT s.slot_date, COALESCE(SUM(p.amount), 0) as daily_total
            FROM bookings b
            JOIN slots s ON b.slot_id = s.slot_id
            LEFT JOIN payments p ON b.booking_id = p.booking_id
            {where_clause}
            GROUP BY s.slot_date
            ORDER BY s.slot_date
        """
        cur.execute(query_daily, tuple(params))
        
        daily_revenue = []
        for row in cur.fetchall():
            daily_revenue.append({'date': row[0], 'revenue': float(row[1])})
            
        cur.close()
        conn.close()
        return {'total_revenue': float(total_revenue), 'daily_revenue': daily_revenue}
    except Exception as e:
        st.error(f"Error fetching revenue stats: {e}")
        return {'total_revenue': 0, 'daily_revenue': []}

def get_cancellation_stats(start_date=None, end_date=None):
    """
    Returns cancellation statistics.
    """
    conn = get_db_connection()
    if not conn:
        return {'total_bookings': 0, 'cancelled_bookings': 0, 'cancellation_rate': 0}
        
    try:
        cur = conn.cursor()
        
        where_clause = ""
        params = []
        
        if start_date and end_date:
            where_clause = " WHERE s.slot_date BETWEEN %s AND %s"
            params.extend([start_date, end_date])
            
        query = f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN b.status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM bookings b
            JOIN slots s ON b.slot_id = s.slot_id
            {where_clause}
        """
        
        cur.execute(query, tuple(params))
        total, cancelled = cur.fetchone()
        
        total = total or 0
        cancelled = cancelled or 0
        rate = (cancelled / total * 100) if total > 0 else 0
        
        cur.close()
        conn.close()
        return {
            'total_bookings': total, 
            'cancelled_bookings': cancelled, 
            'cancellation_rate': round(rate, 2)
        }
    except Exception as e:
        st.error(f"Error fetching cancellation stats: {e}")
        return {'total_bookings': 0, 'cancelled_bookings': 0, 'cancellation_rate': 0}

def get_active_users_count(start_date=None, end_date=None):
    """
    Returns the count of distinct users who have made at least one booking
    within the specified date range.
    """
    conn = get_db_connection()
    if not conn:
        return 0
        
    try:
        cur = conn.cursor()
        
        where_clause = ""
        params = []
        
        if start_date and end_date:
            where_clause = " WHERE s.slot_date BETWEEN %s AND %s"
            params.extend([start_date, end_date])
            
        query = f"""
            SELECT COUNT(DISTINCT b.user_id)
            FROM bookings b
            JOIN slots s ON b.slot_id = s.slot_id
            {where_clause}
        """
        
        cur.execute(query, tuple(params))
        count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        return count or 0
    except Exception as e:
        st.error(f"Error fetching active users count: {e}")
        return 0

def get_peak_hour_insights(start_date=None, end_date=None):
    """
    Returns the number of bookings per hour to identify peak times.
    """
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        cur = conn.cursor()
        
        where_clause = ""
        params = []
        
        if start_date and end_date:
            where_clause = " WHERE s.slot_date BETWEEN %s AND %s"
            params.extend([start_date, end_date])
            
        # Extract hour from start_time. 
        # PostgreSQL: EXTRACT(HOUR FROM s.start_time)
        query = f"""
            SELECT 
                EXTRACT(HOUR FROM s.start_time) as hour,
                COUNT(*) as booking_count
            FROM bookings b
            JOIN slots s ON b.slot_id = s.slot_id
            {where_clause}
            GROUP BY hour
            ORDER BY booking_count DESC
        """
        
        cur.execute(query, tuple(params))
        
        peak_hours = []
        for row in cur.fetchall():
            peak_hours.append({'hour': int(row[0]), 'count': row[1]})
            
        cur.close()
        conn.close()
        return peak_hours
    except Exception as e:
        st.error(f"Error fetching peak hour insights: {e}")
        return []

def check_in_user(qr_code_data, staff_id):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cur = conn.cursor()
        
        # Find booking by QR code
        cur.execute("""
            SELECT booking_id, status FROM bookings WHERE qr_code = %s
        """, (qr_code_data,))
        
        booking = cur.fetchone()
        if not booking:
            return False, "Invalid QR Code"
            
        booking_id, status = booking
        
        if status == 'checked_in':
            return False, "Booking already checked in"
        if status == 'cancelled':
            return False, "Booking is cancelled"
        if status == 'completed':
            return False, "Booking already completed"
            
        # Update status and record check-in
        cur.execute("UPDATE bookings SET status = 'checked_in' WHERE booking_id = %s", (booking_id,))
        
        cur.execute("""
            INSERT INTO qr_checkins (booking_id, staff_id)
            VALUES (%s, %s)
        """, (booking_id, staff_id))

        # Update payment status to 'paid'
        cur.execute("UPDATE payments SET payment_status = 'paid' WHERE booking_id = %s", (booking_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        return True, "Check-in successful"
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Error processing check-in: {e}"

def update_booking_status(booking_id, new_status):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cur = conn.cursor()
        cur.execute("UPDATE bookings SET status = %s WHERE booking_id = %s", (new_status, booking_id))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Status updated successfully"
    except Exception as e:
        return False, f"Error updating status: {e}"
