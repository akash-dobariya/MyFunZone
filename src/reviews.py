
import streamlit as st
from src.database import get_db_connection

def add_review(user_id, game_id, booking_id, rating, feedback):
    """
    Adds a new review to the database.
    Requires at least one of rating or feedback to be present.
    """
    if not rating and not feedback:
        return False, "Please provide either a rating or feedback."
        
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed."
        
    try:
        cur = conn.cursor()
        
        # Check if review already exists for this booking
        cur.execute("SELECT 1 FROM reviews WHERE booking_id = %s", (booking_id,))
        if cur.fetchone():
            return False, "You have already reviewed this booking."
            
        cur.execute("""
            INSERT INTO reviews (user_id, game_id, booking_id, rating, feedback)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, game_id, booking_id, rating, feedback))
        
        conn.commit()
        cur.close()
        conn.close()
        return True, "Review submitted successfully!"
    except Exception as e:
        return False, f"Error submitting review: {e}"

def get_user_reviews(user_id):
    """
    Fetches all reviews submitted by a specific user.
    """
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.*, g.name as game_name
            FROM reviews r
            JOIN games g ON r.game_id = g.game_id
            WHERE r.user_id = %s
            ORDER BY r.created_at DESC
        """, (user_id,))
        
        columns = [desc[0] for desc in cur.description]
        reviews = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        return reviews
    except Exception as e:
        st.error(f"Error fetching reviews: {e}")
        return []

def get_game_reviews(game_id, limit=None, offset=0):
    """
    Fetches reviews for a specific game with optional pagination.
    """
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        cur = conn.cursor()
        query = """
            SELECT r.*, u.username
            FROM reviews r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.game_id = %s
            ORDER BY r.created_at DESC
        """
        params = [game_id]
        
        if limit:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
        cur.execute(query, tuple(params))
        
        columns = [desc[0] for desc in cur.description]
        reviews = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        return reviews
    except Exception as e:
        st.error(f"Error fetching game reviews: {e}")
        return []

def get_game_rating_stats(game_id):
    """
    Returns the average rating and total review count for a game.
    """
    conn = get_db_connection()
    if not conn:
        return {'average_rating': 0, 'total_reviews': 0}
        
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT AVG(rating), COUNT(*)
            FROM reviews
            WHERE game_id = %s AND rating IS NOT NULL
        """, (game_id,))
        
        avg_rating, count = cur.fetchone()
        
        cur.close()
        conn.close()
        return {
            'average_rating': float(avg_rating) if avg_rating else 0.0,
            'total_reviews': count
        }
    except Exception as e:
        st.error(f"Error fetching rating stats: {e}")
        return {'average_rating': 0, 'total_reviews': 0}
