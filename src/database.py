import psycopg2
from psycopg2 import OperationalError
import streamlit as st
from src.utils import hash_password

# Database Configuration
DB_NAME = "myfunzone"
DB_USER = "postgres" 
DB_PASSWORD = "admin"
DB_HOST = "localhost"
DB_PORT = "5432"

def get_db_connection():
    """
    Establishes a connection to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except OperationalError as e:
        st.error(f"Error connecting to the database: {e}")
        st.stop()
        return None

def init_db():
    """
    Initializes the database tables with the final, consolidated schema.
    """
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        
        # 1. Users Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100) UNIQUE,
                phone_number VARCHAR(20) UNIQUE,
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'staff', 'user')),
                is_active BOOLEAN DEFAULT TRUE,
                must_change_password BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Games Table 
        cur.execute("""
            CREATE TABLE IF NOT EXISTS games (
                game_id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                image_url VARCHAR(255),
                category VARCHAR(50) DEFAULT 'General',
                duration_minutes INTEGER,
                base_price DECIMAL(10, 2),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. Slots Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS slots (
                slot_id SERIAL PRIMARY KEY,
                game_id INTEGER REFERENCES games(game_id) ON DELETE CASCADE,
                slot_date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                max_players INTEGER NOT NULL,
                price DECIMAL(10, 2),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. Bookings Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id),
                slot_id INTEGER REFERENCES slots(slot_id),
                number_of_players INTEGER NOT NULL,
                qr_code VARCHAR(255) UNIQUE,
                status VARCHAR(20) CHECK (status IN ('booked', 'checked_in', 'completed', 'cancelled', 'no_show')),
                booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 5. Payments Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id SERIAL PRIMARY KEY,
                booking_id INTEGER REFERENCES bookings(booking_id),
                amount DECIMAL(10, 2) NOT NULL,
                payment_status VARCHAR(20) CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
                payment_method VARCHAR(20),
                payment_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 6. QR Check-ins Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS qr_checkins (
                checkin_id SERIAL PRIMARY KEY,
                booking_id INTEGER REFERENCES bookings(booking_id),
                staff_id INTEGER REFERENCES users(user_id),
                checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 7. Issue Reports Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS issue_reports (
                issue_report_id SERIAL PRIMARY KEY,
                staff_id INTEGER REFERENCES users(user_id),
                game_id INTEGER REFERENCES games(game_id),
                description TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'in_progress')),
                reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 8. Reviews Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                game_id INTEGER REFERENCES games(game_id) ON DELETE CASCADE,
                booking_id INTEGER REFERENCES bookings(booking_id) ON DELETE SET NULL,
                rating INTEGER CHECK (rating BETWEEN 1 AND 5),
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (rating IS NOT NULL OR feedback IS NOT NULL)
            );
        """)

        # 9. Announcements Table 
        cur.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                announcement_id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                target_role VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_pinned BOOLEAN DEFAULT FALSE,
                expires_at DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 10. Announcement Reads Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS announcement_reads (
                announcement_read_id SERIAL PRIMARY KEY,
                announcement_id INTEGER REFERENCES announcements(announcement_id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(announcement_id, user_id)
            );
        """)
        
        cur.execute("SELECT user_id FROM users WHERE username = %s", ('admin',))
        admin = cur.fetchone()
        if not admin:
            hashed_pw = hash_password("admin@987")
            cur.execute("""
                INSERT INTO users (username, password_hash, role, phone_number)
                VALUES (%s, %s, %s, %s)
            """, ('admin', hashed_pw, 'admin', '0000000000'))

        conn.commit()
        cur.close()
        conn.close()
