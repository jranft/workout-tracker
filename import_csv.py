import csv
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import parse_duration, calc_derived
from database import get_db, init_db

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "Workouts - Sheet1.csv")

WORKOUT_TYPE_MAP = {
    "Indoor Walk": "Treadmill",
}

def parse_date(s):
    return datetime.strptime(s.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")

def to_int(s):
    s = s.strip()
    return int(s) if s and s not in ("-",) else None

def to_float(s):
    s = s.strip()
    return float(s) if s and s not in ("-",) else None

def main():
    init_db()
    conn = get_db()

    inserted = 0
    skipped = 0

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)

        for row in reader:
            if len(row) < 10:
                skipped += 1
                continue

            raw_type   = row[1].strip()
            workout_type = WORKOUT_TYPE_MAP.get(raw_type, raw_type)
            workout_date = parse_date(row[0])
            duration     = row[2].strip() or None

            active_calories = to_int(row[4])
            avg_heart_rate  = to_int(row[5])
            max_heart_rate  = to_int(row[6])
            miles           = to_float(row[9])
            avg_cadence     = to_int(row[10])
            peleton_output  = to_int(row[11])
            peleton_resistance = to_int(row[12])
            vo2_max         = to_float(row[15]) if len(row) > 15 else None

            decimal_duration = parse_duration(duration)
            mph, minutes_per_mile, calories_per_minute, calories_per_mile, total_heart_beats, heart_beats_per_mile = calc_derived(
                decimal_duration, miles, active_calories, avg_heart_rate
            )

            conn.execute("""
                INSERT INTO workouts (
                    workout_type, workout_date, duration, decimal_duration,
                    miles, active_calories, avg_heart_rate, max_heart_rate,
                    avg_cadence, peleton_output, peleton_resistance, vo2_max,
                    mph, minutes_per_mile, calories_per_minute, calories_per_mile,
                    total_heart_beats, heart_beats_per_mile, source
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?
                )
            """, (
                workout_type, workout_date, duration, decimal_duration,
                miles, active_calories, avg_heart_rate, max_heart_rate,
                avg_cadence, peleton_output, peleton_resistance, vo2_max,
                mph, minutes_per_mile, calories_per_minute, calories_per_mile,
                total_heart_beats, heart_beats_per_mile, "csv_import",
            ))
            inserted += 1

    conn.commit()
    conn.close()
    print(f"Done: {inserted} rows inserted, {skipped} skipped.")

if __name__ == "__main__":
    main()
