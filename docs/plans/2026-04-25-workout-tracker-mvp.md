# Workout Tracker MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local Flask web app with a form to enter workouts and save them to SQLite.

**Architecture:** Single Flask app with one SQLite database. A `workouts` table stores all entries with a `workout_type` column and type-specific fields. The form uses JavaScript to show/hide relevant fields based on the selected workout type.

**Tech Stack:** Python 3, Flask, SQLite3 (stdlib), Jinja2 templates, vanilla JS/HTML/CSS

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `app.py`
- Create: `database.py`

**Step 1: Initialize git**

```bash
cd /Users/jtr/Projects/workout-tracker
git init
```

**Step 2: Create requirements.txt**

```
flask==3.1.0
```

**Step 3: Create virtual environment and install**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Step 4: Create database.py**

```python
import sqlite3

DB_PATH = "workouts.db"

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
            miles REAL,
            active_calories INTEGER,
            avg_heart_rate INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()
```

**Step 5: Create app.py**

```python
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
```

**Step 6: Commit**

```bash
git add requirements.txt app.py database.py
git commit -m "feat: flask app skeleton with SQLite schema"
```

---

### Task 2: HTML Template

**Files:**
- Create: `templates/index.html`

**Step 1: Create templates directory**

```bash
mkdir -p templates
```

**Step 2: Create templates/index.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Workout Tracker</title>
  <style>
    body { font-family: sans-serif; max-width: 520px; margin: 40px auto; padding: 0 16px; }
    h1 { font-size: 1.5rem; margin-bottom: 24px; }
    label { display: block; margin-top: 14px; font-weight: bold; font-size: 0.9rem; }
    input, select { width: 100%; padding: 8px; margin-top: 4px; box-sizing: border-box; font-size: 1rem; border: 1px solid #ccc; border-radius: 4px; }
    button { margin-top: 24px; padding: 10px 24px; background: #2563eb; color: white; border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; }
    button:hover { background: #1d4ed8; }
    .flash { background: #d1fae5; color: #065f46; padding: 10px; border-radius: 4px; margin-bottom: 16px; }
    .field-group { display: none; }
    .field-group.active { display: block; }
  </style>
</head>
<body>
  <h1>Log Workout</h1>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for msg in messages %}
        <div class="flash">{{ msg }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}

  <form method="POST" action="/log">
    <label>Workout Type
      <select name="workout_type" id="workout_type" required onchange="showFields()">
        <option value="">-- Select --</option>
        {% for wt in workout_types %}
          <option value="{{ wt }}">{{ wt }}</option>
        {% endfor %}
      </select>
    </label>

    <label>Date
      <input type="date" name="workout_date" required>
    </label>

    <!-- Indoor Air Bike fields -->
    <div class="field-group" id="fields-indoor-air-bike">
      <label>Miles
        <input type="number" name="miles" step="0.01" min="0">
      </label>
      <label>Workout Duration (hh:mm:ss)
        <input type="text" name="duration" placeholder="00:20:05" pattern="\d{2}:\d{2}:\d{2}">
      </label>
      <label>Active Calories
        <input type="number" name="active_calories" min="0">
      </label>
      <label>Average Heart Rate (bpm)
        <input type="number" name="avg_heart_rate" min="0">
      </label>
      <label>Start Time
        <input type="time" name="start_time">
      </label>
      <label>End Time
        <input type="time" name="end_time">
      </label>
    </div>

    <button type="submit">Save Workout</button>
  </form>

  <script>
    function showFields() {
      document.querySelectorAll('.field-group').forEach(el => el.classList.remove('active'));
      const val = document.getElementById('workout_type').value;
      if (val === 'Indoor Air Bike') {
        document.getElementById('fields-indoor-air-bike').classList.add('active');
      }
    }
  </script>
</body>
</html>
```

**Step 3: Commit**

```bash
git add templates/
git commit -m "feat: workout entry form with dynamic field display"
```

---

### Task 3: Create .gitignore and Smoke Test

**Files:**
- Create: `.gitignore`

**Step 1: Create .gitignore**

```
venv/
workouts.db
__pycache__/
*.pyc
```

**Step 2: Run the app**

```bash
source venv/bin/activate
python app.py
```

Open http://127.0.0.1:5000 in a browser. Select "Indoor Air Bike" — the workout-specific fields should appear. Fill in and submit; page should reload with "Workout saved!" flash.

**Step 3: Verify data was saved**

```bash
sqlite3 workouts.db "SELECT * FROM workouts;"
```

Expected: one row with your test data.

**Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: add gitignore"
```
