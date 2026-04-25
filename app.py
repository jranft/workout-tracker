import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, get_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

WORKOUT_TYPES = [
    "Indoor Air Bike",
    "Other 1",
    "Other 2",
    "Other 3",
    "Other 4",
    "Other 5",
]

# Fix I3: run init_db at module level so it runs on import, not just under __main__
init_db()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", workout_types=WORKOUT_TYPES)

@app.route("/log", methods=["POST"])
def log_workout():
    data = request.form

    # Fix C2: validate required fields
    workout_type = data.get("workout_type", "").strip()
    workout_date = data.get("workout_date", "").strip()

    if not workout_type or not workout_date:
        flash("Workout type and date are required.")
        return redirect(url_for("index"))

    try:
        datetime.strptime(workout_date, "%Y-%m-%d")
    except ValueError:
        flash("Invalid date format. Please use YYYY-MM-DD.")
        return redirect(url_for("index"))

    # Fix C1: wrap type conversions and INSERT in try/except for ValueError/KeyError
    # Fix I2: use try/finally to ensure conn.close() is always called
    conn = get_db()
    try:
        try:
            miles = float(data["miles"]) if data.get("miles") else None
            active_calories = int(data["active_calories"]) if data.get("active_calories") else None
            avg_heart_rate = int(data["avg_heart_rate"]) if data.get("avg_heart_rate") else None
        except (ValueError, KeyError):
            flash("Invalid numeric input for miles, calories, or heart rate.")
            return redirect(url_for("index"))

        conn.execute("""
            INSERT INTO workouts
                (workout_type, workout_date, start_time, end_time, duration, miles, active_calories, avg_heart_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workout_type,
            workout_date,
            data.get("start_time") or None,
            data.get("end_time") or None,
            data.get("duration") or None,
            miles,
            active_calories,
            avg_heart_rate,
        ))
        conn.commit()
    finally:
        conn.close()

    flash("Workout saved!")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
