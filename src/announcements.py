import streamlit as st
from src.database import get_db_connection
from datetime import date, datetime

def create_announcement(title, content, target_role, is_pinned=False, expires_at=None):
    """
    Creates a new announcement.
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed."
        
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO announcements (title, content, target_role, is_pinned, expires_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, content, target_role, is_pinned, expires_at))
        
        conn.commit()
        cur.close()
        conn.close()
        return True, "Announcement created successfully!"
    except Exception as e:
        return False, f"Error creating announcement: {e}"

def get_announcements_for_role(role, user_id=None):
    """
    Fetches active announcements for a specific role.
    Sorts by Pinned first, then Created At desc.
    If user_id is provided, also returns read status.
    """
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        cur = conn.cursor()
        
        query = """
            SELECT a.*, 
                   CASE WHEN ar.read_at IS NOT NULL THEN TRUE ELSE FALSE END as is_read,
                   ar.read_at
            FROM announcements a
            LEFT JOIN announcement_reads ar ON a.announcement_id = ar.announcement_id AND ar.user_id = %s
            WHERE (a.target_role = 'all' OR a.target_role = %s)
            AND a.is_active = TRUE
            AND (a.expires_at IS NULL OR a.expires_at >= CURRENT_DATE)
            ORDER BY a.is_pinned DESC, a.created_at DESC
        """
        
        cur.execute(query, (user_id, role))
        
        columns = [desc[0] for desc in cur.description]
        announcements = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        return announcements
    except Exception as e:
        st.error(f"Error fetching announcements: {e}")
        return []

def mark_announcement_as_read(announcement_id, user_id):
    """
    Marks an announcement as read for a specific user.
    """
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        cur = conn.cursor()
        
        # Check if already read
        cur.execute("""
            INSERT INTO announcement_reads (announcement_id, user_id)
            VALUES (%s, %s)
            ON CONFLICT (announcement_id, user_id) DO NOTHING
        """, (announcement_id, user_id))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error marking as read: {e}")
        return False

def get_all_announcements():
    """
    Fetches all announcements for admin management.
    """
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM announcements ORDER BY created_at DESC
        """)
        columns = [desc[0] for desc in cur.description]
        announcements = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        conn.close()
        return announcements
    except Exception as e:
        st.error(f"Error fetching all announcements: {e}")
        return []

def get_announcement_read_stats(announcement_id):
    """
    Returns read stats for an announcement:
    - List of users who read it
    - List of users who haven't read it (filtered by target role)
    """
    conn = get_db_connection()
    if not conn:
        return {'read': [], 'unread': []}
        
    try:
        cur = conn.cursor()
        
        # Get target role first
        cur.execute("SELECT target_role FROM announcements WHERE announcement_id = %s", (announcement_id,))
        result = cur.fetchone()
        if not result:
            return {'read': [], 'unread': []}
        
        target_role = result[0]
        
        # Get readers
        cur.execute("""
            SELECT u.username, u.role, ar.read_at
            FROM announcement_reads ar
            JOIN users u ON ar.user_id = u.user_id
            WHERE ar.announcement_id = %s
        """, (announcement_id,))
        read_columns = [desc[0] for desc in cur.description]
        read_users = [dict(zip(read_columns, row)) for row in cur.fetchall()]
        
        # Get unread users
        # Filter users based on target_role
        role_filter = ""
        params = [announcement_id]
        
        if target_role != 'all':
            role_filter = "AND u.role = %s"
            params.append(target_role)
            
        cur.execute(f"""
            SELECT u.username, u.role
            FROM users u
            WHERE u.user_id NOT IN (
                SELECT user_id FROM announcement_reads WHERE announcement_id = %s
            )
            {role_filter}
            AND u.is_active = TRUE
        """, tuple(params))
        
        unread_columns = [desc[0] for desc in cur.description]
        unread_users = [dict(zip(unread_columns, row)) for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        return {'read': read_users, 'unread': unread_users}
        
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return {'read': [], 'unread': []}
