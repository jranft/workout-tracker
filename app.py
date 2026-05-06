import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, get_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

@app.template_filter('pace')
def format_pace(val):
    if val is None:
        return ''
    mins = int(val)
    secs = round((val - mins) * 60)
    if secs == 60:
        mins += 1
        secs = 0
    return f'{mins}:{secs:02d}'

@app.template_filter('dec')
def format_decimal(val):
    if val is None:
        return ''
    return f'{val:.2f}'

@app.template_filter('format_time')
def format_time(time_str):
    if not time_str:
        return ''
    try:
        dt = datetime.strptime(time_str, '%H:%M')
        return dt.strftime('%I:%M %p').lstrip('0')
    except (ValueError, TypeError):
        return time_str

@app.template_filter('one_dec')
def format_one_decimal(val):
    if val is None:
        return ''
    return f'{val:.1f}'

@app.template_filter('format_date')
def format_date(date_str):
    if not date_str:
        return ''
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%B %d, %Y')
    except (ValueError, TypeError):
        return date_str

def parse_duration(s):
    if not s:
        return None
    try:
        parts = s.strip().split(":")
        if len(parts) != 3:
            return None
        h, m, sec = int(parts[0]), int(parts[1]), int(parts[2])
        if h < 0:
            return None
        if not (0 <= m <= 59 and 0 <= sec <= 59):
            return None
        return h * 60 + m + sec / 60
    except (ValueError, AttributeError):
        return None

def calc_derived(decimal_duration, miles, active_calories, avg_heart_rate):
    d, m, c, hr = decimal_duration, miles, active_calories, avg_heart_rate
    mph = round(m / (d / 60), 4) if m and d else None
    minutes_per_mile = round(d / m, 4) if m and d else None
    calories_per_minute = round(c / d, 4) if c and d else None
    calories_per_mile = round(c / m, 4) if c and m else None
    total_heart_beats = round(hr * d) if hr and d else None
    heart_beats_per_mile = round((hr * d) / m) if hr and d and m else None
    return mph, minutes_per_mile, calories_per_minute, calories_per_mile, total_heart_beats, heart_beats_per_mile

WORKOUT_TYPES = [
    "Air Bike",
    "Elliptical",
    "Indoor Cycle",
    "Outdoor Cycle",
    "Outdoor Run",
    "Outdoor Walk",
    "Peleton",
    "Rowing",
    "Stair Stepper",
    "Treadmill",
]

# Fix I3: run init_db at module level so it runs on import, not just under __main__
init_db()

@app.route("/", methods=["GET"])
def index():
    conn = get_db()
    try:
        workouts = conn.execute(
            "SELECT * FROM workouts ORDER BY workout_date DESC, id DESC"
        ).fetchall()
    finally:
        conn.close()
    return render_template("home.html", workouts=workouts)

@app.route("/new", methods=["GET"])
def new_workout():
    return render_template("index.html", workout_types=WORKOUT_TYPES)

@app.route("/edit/<int:workout_id>", methods=["GET"])
def edit_workout(workout_id):
    conn = get_db()
    try:
        workout = conn.execute(
            "SELECT * FROM workouts WHERE id = ?", (workout_id,)
        ).fetchone()
    finally:
        conn.close()
    if workout is None:
        flash("Workout not found.")
        return redirect(url_for("index"))
    return render_template("edit.html", workout=workout, workout_types=WORKOUT_TYPES)

@app.route("/log", methods=["POST"])
def log_workout():
    data = request.form

    # Fix C2: validate required fields
    workout_type = data.get("workout_type", "").strip()
    workout_date = data.get("workout_date", "").strip()

    if not workout_type or not workout_date:
        flash("Workout type and date are required.")
        return redirect(url_for("new_workout"))

    try:
        datetime.strptime(workout_date, "%Y-%m-%d")
    except ValueError:
        flash("Invalid date format. Please use YYYY-MM-DD.")
        return redirect(url_for("new_workout"))

    # Fix C1: wrap type conversions and INSERT in try/except for ValueError/KeyError
    # Fix I2: use try/finally to ensure conn.close() is always called
    conn = get_db()
    try:
        try:
            meters = int(data["meters"]) if data.get("meters") else None
            elevation_gain = int(data["elevation_gain"]) if data.get("elevation_gain") else None
            flights = int(data["flights"]) if data.get("flights") else None
            miles = float(data["miles"]) if data.get("miles") else None
            active_calories = int(data["active_calories"]) if data.get("active_calories") else None
            avg_heart_rate = int(data["avg_heart_rate"]) if data.get("avg_heart_rate") else None
            max_heart_rate = int(data["max_heart_rate"]) if data.get("max_heart_rate") else None
            avg_cadence = int(data["avg_cadence"]) if data.get("avg_cadence") else None
            vo2_max = float(data["vo2_max"]) if data.get("vo2_max") else None
            peleton_output = int(data["peleton_output"]) if data.get("peleton_output") else None
            peleton_resistance = int(data["peleton_resistance"]) if data.get("peleton_resistance") else None
            avg_power = int(data["avg_power"]) if data.get("avg_power") else None
        except (ValueError, KeyError):
            flash("Invalid numeric input for miles, calories, heart rate, or cadence.")
            return redirect(url_for("new_workout"))

        duration = data.get("duration") or None
        decimal_duration = parse_duration(duration) if duration else None
        mph, minutes_per_mile, calories_per_minute, calories_per_mile, total_heart_beats, heart_beats_per_mile = \
            calc_derived(decimal_duration, miles, active_calories, avg_heart_rate)

        conn.execute("""
            INSERT INTO workouts
                (workout_type, workout_date, start_time, end_time, duration, decimal_duration,
                 meters, elevation_gain, flights, miles, active_calories, avg_heart_rate, max_heart_rate, avg_cadence,
                 vo2_max, peleton_output, peleton_resistance, avg_power,
                 mph, minutes_per_mile, calories_per_minute, calories_per_mile,
                 total_heart_beats, heart_beats_per_mile)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workout_type, workout_date,
            data.get("start_time") or None,
            data.get("end_time") or None,
            duration, decimal_duration,
            meters, elevation_gain, flights, miles, active_calories, avg_heart_rate, max_heart_rate, avg_cadence,
            vo2_max, peleton_output, peleton_resistance, avg_power,
            mph, minutes_per_mile, calories_per_minute, calories_per_mile,
            total_heart_beats, heart_beats_per_mile,
        ))
        conn.commit()
    finally:
        conn.close()

    flash("Workout saved!")
    return redirect(url_for("index"))

@app.route("/edit/<int:workout_id>", methods=["POST"])
def update_workout(workout_id):
    data = request.form
    workout_type = data.get("workout_type", "").strip()
    workout_date = data.get("workout_date", "").strip()

    if not workout_type or not workout_date:
        flash("Workout type and date are required.")
        return redirect(url_for("edit_workout", workout_id=workout_id))

    try:
        datetime.strptime(workout_date, "%Y-%m-%d")
    except ValueError:
        flash("Invalid date format. Please use YYYY-MM-DD.")
        return redirect(url_for("edit_workout", workout_id=workout_id))

    conn = get_db()
    try:
        try:
            meters = int(data["meters"]) if data.get("meters") else None
            elevation_gain = int(data["elevation_gain"]) if data.get("elevation_gain") else None
            flights = int(data["flights"]) if data.get("flights") else None
            miles = float(data["miles"]) if data.get("miles") else None
            active_calories = int(data["active_calories"]) if data.get("active_calories") else None
            avg_heart_rate = int(data["avg_heart_rate"]) if data.get("avg_heart_rate") else None
            max_heart_rate = int(data["max_heart_rate"]) if data.get("max_heart_rate") else None
            avg_cadence = int(data["avg_cadence"]) if data.get("avg_cadence") else None
            vo2_max = float(data["vo2_max"]) if data.get("vo2_max") else None
            peleton_output = int(data["peleton_output"]) if data.get("peleton_output") else None
            peleton_resistance = int(data["peleton_resistance"]) if data.get("peleton_resistance") else None
            avg_power = int(data["avg_power"]) if data.get("avg_power") else None
        except (ValueError, KeyError):
            flash("Invalid numeric input for miles, calories, heart rate, or cadence.")
            return redirect(url_for("edit_workout", workout_id=workout_id))

        duration = data.get("duration") or None
        decimal_duration = parse_duration(duration) if duration else None
        mph, minutes_per_mile, calories_per_minute, calories_per_mile, total_heart_beats, heart_beats_per_mile = \
            calc_derived(decimal_duration, miles, active_calories, avg_heart_rate)

        conn.execute("""
            UPDATE workouts SET
                workout_type=?, workout_date=?, start_time=?, end_time=?,
                duration=?, decimal_duration=?, meters=?, elevation_gain=?, flights=?,
                miles=?, active_calories=?, avg_heart_rate=?, max_heart_rate=?, avg_cadence=?,
                vo2_max=?, peleton_output=?, peleton_resistance=?, avg_power=?,
                mph=?, minutes_per_mile=?, calories_per_minute=?, calories_per_mile=?,
                total_heart_beats=?, heart_beats_per_mile=?
            WHERE id=?
        """, (
            workout_type, workout_date,
            data.get("start_time") or None,
            data.get("end_time") or None,
            duration, decimal_duration,
            meters, elevation_gain, flights, miles, active_calories, avg_heart_rate, max_heart_rate, avg_cadence,
            vo2_max, peleton_output, peleton_resistance, avg_power,
            mph, minutes_per_mile, calories_per_minute, calories_per_mile,
            total_heart_beats, heart_beats_per_mile,
            workout_id,
        ))
        conn.commit()
    finally:
        conn.close()

    flash("Workout updated!")
    return redirect(url_for("index"))

@app.route("/delete/<int:workout_id>", methods=["POST"])
def delete_workout(workout_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
        conn.commit()
    finally:
        conn.close()
    flash("Workout deleted.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
