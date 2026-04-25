from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, get_db

app = Flask(__name__)
app.secret_key = "dev-secret-key"

WORKOUT_TYPES = [
    "Indoor Air Bike",
    "Other 1",
    "Other 2",
    "Other 3",
    "Other 4",
    "Other 5",
]

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", workout_types=WORKOUT_TYPES)

@app.route("/log", methods=["POST"])
def log_workout():
    data = request.form
    conn = get_db()
    conn.execute("""
        INSERT INTO workouts
            (workout_type, workout_date, start_time, end_time, duration, miles, active_calories, avg_heart_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("workout_type"),
        data.get("workout_date"),
        data.get("start_time") or None,
        data.get("end_time") or None,
        data.get("duration") or None,
        float(data["miles"]) if data.get("miles") else None,
        int(data["active_calories"]) if data.get("active_calories") else None,
        int(data["avg_heart_rate"]) if data.get("avg_heart_rate") else None,
    ))
    conn.commit()
    conn.close()
    flash("Workout saved!")
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
