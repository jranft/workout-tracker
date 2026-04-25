import os
import sqlite3

# Fix m1: use absolute path so the DB is always found regardless of cwd
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workouts.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_type TEXT NOT NULL,
            workout_date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            duration TEXT,
            decimal_duration REAL,
            miles REAL,
            active_calories INTEGER,
            avg_heart_rate INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    try:
        conn.execute("ALTER TABLE workouts ADD COLUMN decimal_duration REAL")
    except Exception:
        pass
    conn.commit()
    conn.close()
