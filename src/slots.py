from src.database import get_db_connection
import streamlit as st
from datetime import datetime, date, timedelta

def create_slot(game_id, slot_date, start_time, end_time, max_players, price, is_active=True):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO slots (game_id, slot_date, start_time, end_time, max_players, price, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (game_id, slot_date, start_time, end_time, max_players, price, is_active))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Slot created successfully"
    except Exception as e:
        return False, f"Error creating slot: {e}"

def create_slots_range(game_id, start_date, end_date, start_time, end_time, max_players, price, is_active=True):
    if start_date > end_date:
        return False, "Start date cannot be after end date"
    
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
        
    try:
        cur = conn.cursor()
        
        # Calculate number of days
        delta = end_date - start_date
        
        created_count = 0
        for i in range(delta.days + 1):
            current_date = start_date + timedelta(days=i)
            cur.execute("""
                INSERT INTO slots (game_id, slot_date, start_time, end_time, max_players, price, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (game_id, current_date, start_time, end_time, max_players, price, is_active))
            created_count += 1
            
        conn.commit()
        cur.close()
        conn.close()
        return True, f"Successfully created {created_count} slots from {start_date} to {end_date}"
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Error creating slots: {e}"

def get_slots_by_game(game_id, date_filter=None):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        query = "SELECT * FROM slots WHERE game_id = %s"
        params = [game_id]
        
        if date_filter:
            query += " AND slot_date = %s"
            params.append(date_filter)
            
        query += " ORDER BY slot_date, start_time"
        
        cur.execute(query, tuple(params))
        
        slots = []
        columns = [desc[0] for desc in cur.description]
        for row in cur.fetchall():
            slots.append(dict(zip(columns, row)))
            
        cur.close()
        conn.close()
        return slots
    except Exception as e:
        st.error(f"Error fetching slots: {e}")
        return []

def get_available_slots(game_id, target_date=None, include_full=False):
    if target_date is None:
        target_date = date.today()
        
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        # Get slots that are active and have available space
        # Need to join with bookings to count current bookings
        query = """
            SELECT s.*, 
                   (s.max_players - COALESCE(SUM(b.number_of_players), 0)) as available_spots
            FROM slots s
            LEFT JOIN bookings b ON s.slot_id = b.slot_id AND b.status IN ('booked', 'checked_in')
            WHERE s.game_id = %s 
              AND s.slot_date = %s 
              AND s.is_active = TRUE
            GROUP BY s.slot_id
        """
        
        if not include_full:
            query += " HAVING (s.max_players - COALESCE(SUM(b.number_of_players), 0)) > 0"
            
        query += " ORDER BY s.start_time"
        
        cur.execute(query, (game_id, target_date))
        
        slots = []
        columns = [desc[0] for desc in cur.description]
        for row in cur.fetchall():
            slots.append(dict(zip(columns, row)))
            
        cur.close()
        conn.close()
        return slots
    except Exception as e:
        st.error(f"Error fetching available slots: {e}")
        return []

def delete_slot(slot_id):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM slots WHERE slot_id = %s", (slot_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Slot deleted successfully"
    except Exception as e:
        return False, f"Error deleting slot: {e}"

def toggle_slot_active(slot_id, is_active):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cur = conn.cursor()
        cur.execute("UPDATE slots SET is_active = %s WHERE slot_id = %s", (is_active, slot_id))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Slot status updated successfully"
    except Exception as e:
        return False, f"Error updating slot status: {e}"
