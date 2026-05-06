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
            max_heart_rate INTEGER,
            avg_cadence INTEGER,
            meters INTEGER,
            elevation_gain INTEGER,
            flights INTEGER,
            mph REAL,
            minutes_per_mile REAL,
            calories_per_minute REAL,
            calories_per_mile REAL,
            total_heart_beats INTEGER,
            heart_beats_per_mile INTEGER,
            vo2_max REAL,
            peleton_output INTEGER,
            peleton_resistance INTEGER,
            avg_power INTEGER,
            source TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    try:
        conn.execute("ALTER TABLE workouts ADD COLUMN decimal_duration REAL")
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e):
            raise
    try:
        conn.execute("ALTER TABLE workouts ADD COLUMN max_heart_rate INTEGER")
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e):
            raise
    try:
        conn.execute("ALTER TABLE workouts ADD COLUMN avg_cadence INTEGER")
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e):
            raise
    for col, typ in [
        ("meters", "INTEGER"), ("elevation_gain", "INTEGER"), ("flights", "INTEGER"), ("mph", "REAL"), ("minutes_per_mile", "REAL"), ("calories_per_minute", "REAL"),
        ("calories_per_mile", "REAL"), ("total_heart_beats", "INTEGER"), ("heart_beats_per_mile", "INTEGER"),
        ("vo2_max", "REAL"),
        ("peleton_output", "INTEGER"),
        ("peleton_resistance", "INTEGER"),
        ("avg_power", "INTEGER"),
        ("source", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE workouts ADD COLUMN {col} {typ}")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e):
                raise
    conn.commit()
    conn.close()
