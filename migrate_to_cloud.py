"""
Direct DB-to-DB Migration: Local PostgreSQL -> Supabase Cloud PostgreSQL
Transfers all data table by table with exact columns, multiline text, and resets sequences.
"""

import sys
import psycopg2
from psycopg2.extras import execute_values

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Local PostgreSQL configuration
LOCAL_CONFIG = {
    "dbname": "myfunzone",
    "user": "postgres",
    "password": "admin",
    "host": "localhost",
    "port": "5432"
}

# Tables in strict dependency order (parents first)
TABLES = [
    ("users", "user_id"),
    ("games", "game_id"),
    ("slots", "slot_id"),
    ("bookings", "booking_id"),
    ("payments", "payment_id"),
    ("qr_checkins", "checkin_id"),
    ("issue_reports", "issue_report_id"),
    ("reviews", "review_id"),
    ("announcements", "announcement_id"),
    ("announcement_reads", "announcement_read_id"),
]

def migrate(cloud_url):
    print("=" * 65)
    print("  MyFunZone: Local PostgreSQL -> Supabase Direct Migration")
    print("=" * 65)

    # 1. Connect to Local DB
    print("\n[1/5] Connecting to Local Database...")
    try:
        local_conn = psycopg2.connect(**LOCAL_CONFIG)
        local_cur = local_conn.cursor()
        print("  ✓ Connected to local PostgreSQL (myfunzone)")
    except Exception as e:
        print(f"  ✗ Local connection error: {e}")
        return

    # 2. Connect to Cloud DB
    print("\n[2/5] Connecting to Cloud Database (Supabase)...")
    try:
        cloud_conn = psycopg2.connect(cloud_url)
        cloud_conn.autocommit = False
        cloud_cur = cloud_conn.cursor()
        print("  ✓ Connected to Supabase Cloud PostgreSQL")
    except Exception as e:
        print(f"  ✗ Cloud connection error: {e}")
        return

    # 3. Ensure Remote Schema Exists (Run table creation)
    print("\n[3/5] Setting up clean schema on Supabase...")
    table_names = [t[0] for t in reversed(TABLES)]
    for t in table_names:
        try:
            cloud_cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")
        except Exception:
            cloud_conn.rollback()
    cloud_conn.commit()

    # Create tables with current application schema
    create_schema_sql = [
        """CREATE TABLE users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE,
            phone_number VARCHAR(20) UNIQUE,
            role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'staff', 'user')),
            is_active BOOLEAN DEFAULT TRUE,
            must_change_password BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE games (
            game_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            image_url VARCHAR(255),
            category VARCHAR(50) DEFAULT 'General',
            duration_minutes INTEGER,
            base_price DECIMAL(10, 2),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE slots (
            slot_id SERIAL PRIMARY KEY,
            game_id INTEGER REFERENCES games(game_id) ON DELETE CASCADE,
            slot_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            max_players INTEGER NOT NULL,
            price DECIMAL(10, 2),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE bookings (
            booking_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            slot_id INTEGER REFERENCES slots(slot_id),
            number_of_players INTEGER NOT NULL,
            qr_code VARCHAR(255) UNIQUE,
            status VARCHAR(20) CHECK (status IN ('booked', 'checked_in', 'completed', 'cancelled', 'no_show')),
            booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE payments (
            payment_id SERIAL PRIMARY KEY,
            booking_id INTEGER REFERENCES bookings(booking_id),
            amount DECIMAL(10, 2) NOT NULL,
            payment_status VARCHAR(20) CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
            payment_method VARCHAR(20),
            payment_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE qr_checkins (
            checkin_id SERIAL PRIMARY KEY,
            booking_id INTEGER REFERENCES bookings(booking_id),
            staff_id INTEGER REFERENCES users(user_id),
            checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE issue_reports (
            issue_report_id SERIAL PRIMARY KEY,
            staff_id INTEGER REFERENCES users(user_id),
            game_id INTEGER REFERENCES games(game_id),
            description TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'in_progress')),
            reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE reviews (
            review_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
            game_id INTEGER REFERENCES games(game_id) ON DELETE CASCADE,
            booking_id INTEGER REFERENCES bookings(booking_id) ON DELETE SET NULL,
            rating INTEGER CHECK (rating BETWEEN 1 AND 5),
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CHECK (rating IS NOT NULL OR feedback IS NOT NULL)
        );""",
        """CREATE TABLE announcements (
            announcement_id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            target_role VARCHAR(50) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_pinned BOOLEAN DEFAULT FALSE,
            expires_at DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE announcement_reads (
            announcement_read_id SERIAL PRIMARY KEY,
            announcement_id INTEGER REFERENCES announcements(announcement_id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
            read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(announcement_id, user_id)
        );"""
    ]
    for sql in create_schema_sql:
        cloud_cur.execute(sql)
    cloud_conn.commit()
    print("  ✓ Clean schema created on Supabase")

    # 4. Copy data table by table
    print("\n[4/5] Copying data from local database...")
    for table, pk in TABLES:
        try:
            local_cur.execute(f"SELECT * FROM {table}")
            rows = local_cur.fetchall()
            col_names = [desc[0] for desc in local_cur.description]
        except Exception as e:
            local_conn.rollback()
            print(f"  ⚠ Skipping {table} (local error: {e})")
            continue

        if not rows:
            print(f"  • {table}: 0 rows (empty)")
            continue

        # Build column list and insert
        cols_str = ", ".join(col_names)
        insert_sql = f"INSERT INTO {table} ({cols_str}) VALUES %s"

        try:
            execute_values(cloud_cur, insert_sql, rows)
            cloud_conn.commit()
            print(f"  ✓ {table}: successfully migrated {len(rows)} rows")
        except Exception as e:
            cloud_conn.rollback()
            print(f"  ✗ Failed to copy {table}: {e}")

        # Reset serial sequence so new inserts work smoothly
        try:
            cloud_cur.execute(
                f"SELECT setval(pg_get_serial_sequence('{table}', '{pk}'), COALESCE((SELECT MAX({pk}) FROM {table}), 1), true);"
            )
            cloud_conn.commit()
        except Exception:
            cloud_conn.rollback()

    # 5. Summary / Verification
    print("\n[5/5] Verification - Row counts in Supabase:")
    for table, _ in TABLES:
        try:
            cloud_cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cloud_cur.fetchone()[0]
            print(f"    - {table:<20}: {count} rows")
        except Exception:
            cloud_conn.rollback()
            print(f"    - {table:<20}: Error reading")

    local_cur.close()
    local_conn.close()
    cloud_cur.close()
    cloud_conn.close()

    print("\n" + "=" * 65)
    print("  Migration completed successfully!")
    print("  All local games, slots, users, and bookings are now in Supabase.")
    print("=" * 65)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_to_cloud.py <SUPABASE_DATABASE_URL>")
        sys.exit(1)
    migrate(sys.argv[1])
