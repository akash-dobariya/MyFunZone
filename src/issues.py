from src.database import get_db_connection
import streamlit as st

def create_issue_report(staff_id, game_id, description):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO issue_reports (staff_id, game_id, description, status)
            VALUES (%s, %s, %s, 'open')
        """, (staff_id, game_id, description))
        
        conn.commit()
        cur.close()
        conn.close()
        return True, "Issue reported successfully"
    except Exception as e:
        return False, f"Error reporting issue: {e}"

def get_issue_reports(status_filter=None):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        query = """
            SELECT r.*, u.username as staff_name, g.name as game_name
            FROM issue_reports r
            JOIN users u ON r.staff_id = u.user_id
            LEFT JOIN games g ON r.game_id = g.game_id
        """
        params = []
        
        if status_filter:
            query += " WHERE r.status = %s"
            params.append(status_filter)
            
        query += " ORDER BY r.reported_at DESC"
        
        cur.execute(query, tuple(params))
        
        reports = []
        columns = [desc[0] for desc in cur.description]
        for row in cur.fetchall():
            reports.append(dict(zip(columns, row)))
            
        cur.close()
        conn.close()
        return reports
    except Exception as e:
        st.error(f"Error fetching reports: {e}")
        return []

def update_issue_status(report_id, new_status):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE issue_reports SET status = %s WHERE issue_report_id = %s
        """, (new_status, report_id))
        
        conn.commit()
        cur.close()
        conn.close()
        return True, "Status updated successfully"
    except Exception as e:
        return False, f"Error updating status: {e}"
