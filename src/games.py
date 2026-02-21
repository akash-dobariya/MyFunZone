from src.database import get_db_connection
import streamlit as st

def add_game(name, description, image_url, duration_minutes, base_price, category='General'):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO games (name, description, image_url, duration_minutes, base_price, category)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, description, image_url, duration_minutes, base_price, category))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Game added successfully"
    except Exception as e:
        return False, f"Error adding game: {e}"

def get_all_games(active_only=True, category=None):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        query = "SELECT * FROM games WHERE 1=1"
        params = []
        
        if active_only:
            query += " AND is_active = TRUE"
            
        if category and category != 'All':
            query += " AND category = %s"
            params.append(category)
            
        query += " ORDER BY game_id DESC"
        
        cur.execute(query, tuple(params))
        
        games = []
        columns = [desc[0] for desc in cur.description]
        for row in cur.fetchall():
            games.append(dict(zip(columns, row)))
            
        cur.close()
        conn.close()
        return games
    except Exception as e:
        st.error(f"Error fetching games: {e}")
        return []

def update_game(game_id, name, description, image_url, duration_minutes, base_price, is_active, category):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE games 
            SET name=%s, description=%s, image_url=%s, duration_minutes=%s, base_price=%s, is_active=%s, category=%s
            WHERE game_id=%s
        """, (name, description, image_url, duration_minutes, base_price, is_active, category, game_id))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Game updated successfully"
    except Exception as e:
        return False, f"Error updating game: {e}"

def deactivate_game(game_id):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cur = conn.cursor()
        cur.execute("UPDATE games SET is_active = FALSE WHERE game_id = %s", (game_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Game deactivated successfully"
    except Exception as e:
        return False, f"Error deactivating game: {e}"

def activate_game(game_id):
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    
    try:
        cur = conn.cursor()
        cur.execute("UPDATE games SET is_active = TRUE WHERE game_id = %s", (game_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True, "Game activated successfully"
    except Exception as e:
        return False, f"Error activating game: {e}"
