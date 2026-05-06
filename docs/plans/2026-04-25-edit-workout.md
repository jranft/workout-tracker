# Edit Workout Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow editing and deleting a workout by clicking its row in the home page table, opening a pre-populated edit form at `/edit/<id>` with Update and Delete buttons.

**Architecture:** Add `GET /edit/<id>` to load workout data and render a new `edit.html` template (mirrors the new-workout form but pre-populated). Add `POST /edit/<id>` to update the row. Add `POST /delete/<id>` to delete the row (JS confirm dialog on the button, no separate confirmation page). Both POST handlers redirect to `/` on success. Make table rows in `home.html` clickable by wrapping each `<tr>` with an `onclick` that navigates to `/edit/<id>`.

**Tech Stack:** Flask, SQLite, Jinja2, vanilla JS

---

### Task 1: Make table rows clickable in home.html

**Files:**
- Modify: `templates/home.html`

**Step 1: Add cursor style and onclick to each `<tr>` in the tbody**

In `templates/home.html`, change the tbody row from:
```html
      {% for w in workouts %}
      <tr>
```
to:
```html
      {% for w in workouts %}
      <tr style="cursor:pointer;" onclick="location.href='/edit/{{ w.id }}'">
```

Also add a hover style to make rows feel clickable. The existing `tr:hover td { background: #f9fafb; }` CSS already handles this — no change needed.

**Step 2: Verify in browser**

```bash
source venv/bin/activate && PORT=5001 python app.py &
# visit http://127.0.0.1:5001/ and hover over rows — cursor should change to pointer
# click a row — should 404 (edit route not yet added)
kill %1
```

**Step 3: Commit**

```bash
git add templates/home.html
git commit -m "feat: make workout table rows clickable"
```

---

### Task 2: Add GET /edit/<id> route and edit.html template

**Files:**
- Modify: `app.py`
- Create: `templates/edit.html`

**Step 1: Add the GET route to app.py**

Add this route after `new_workout` in `app.py`:

```python
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
```

**Step 2: Create templates/edit.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light">
  <title>Edit Workout</title>
  <style>
    html { color-scheme: light; }
    body { font-family: sans-serif; max-width: 520px; margin: 40px auto; padding: 0 16px; background: #ffffff; color: #111; }
    .back-link { font-size: 0.9rem; color: #2563eb; }
    h1 { font-size: 1.5rem; margin-bottom: 24px; }
    label { display: block; margin-top: 14px; font-weight: bold; font-size: 0.9rem; }
    input, select { width: 100%; padding: 8px; margin-top: 4px; box-sizing: border-box; font-size: 1rem; border: 1px solid #ccc; border-radius: 4px; }
    .actions { display: flex; gap: 12px; margin-top: 24px; }
    .btn-update { padding: 10px 24px; background: #2563eb; color: white; border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; }
    .btn-update:hover { background: #1d4ed8; }
    .btn-delete { padding: 10px 24px; background: #dc2626; color: white; border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; }
    .btn-delete:hover { background: #b91c1c; }
    .flash { background: #d1fae5; color: #065f46; padding: 10px; border-radius: 4px; margin-bottom: 16px; }
    .field-group { display: none; }
    .field-group.active { display: block; }
  </style>
</head>
<body>
  <a href="{{ url_for('index') }}" class="back-link">&larr; Home</a>
  <h1>Edit Workout</h1>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for msg in messages %}
        <div class="flash">{{ msg }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}

  <form method="POST" action="{{ url_for('update_workout', workout_id=workout.id) }}">
    <label>Workout Type
      <select name="workout_type" id="workout_type" required onchange="showFields()">
        <option value="">-- Select --</option>
        {% for wt in workout_types %}
          <option value="{{ wt }}" {% if wt == workout.workout_type %}selected{% endif %}>{{ wt }}</option>
        {% endfor %}
      </select>
    </label>

    <label>Date
      <input type="date" name="workout_date" value="{{ workout.workout_date }}" required>
    </label>

    <!-- Indoor Air Bike fields -->
    <div class="field-group" id="fields-indoor-air-bike">
      <label>Miles
        <input type="number" name="miles" step="0.01" min="0" value="{{ workout.miles if workout.miles is not none else '' }}">
      </label>
      <label>Workout Duration (hh:mm:ss)
        <input type="text" name="duration" id="duration" placeholder="00:20:05" pattern="\d{2}:\d{2}:\d{2}" oninput="updateDecimal()" value="{{ workout.duration or '' }}">
      </label>
      <span id="decimal-duration" style="display:none; font-size:0.85rem; color:#555; margin-top:4px;">
        Decimal minutes: <strong id="decimal-value"></strong>
      </span>
      <label>Active Calories
        <input type="number" name="active_calories" min="0" value="{{ workout.active_calories if workout.active_calories is not none else '' }}">
      </label>
      <label>Average Heart Rate (bpm)
        <input type="number" name="avg_heart_rate" min="0" value="{{ workout.avg_heart_rate if workout.avg_heart_rate is not none else '' }}">
      </label>
      <label>Start Time
        <input type="time" name="start_time" value="{{ workout.start_time or '' }}">
      </label>
      <label>End Time
        <input type="time" name="end_time" value="{{ workout.end_time or '' }}">
      </label>
    </div>

    <div class="actions">
      <button type="submit" class="btn-update">Update</button>
    </div>
  </form>

  <form method="POST" action="{{ url_for('delete_workout', workout_id=workout.id) }}" style="margin-top:0;">
    <button type="submit" class="btn-delete" onclick="return confirm('Delete this workout? This cannot be undone.')">Delete</button>
  </form>

  <script>
    function toSlug(s) {
      return s.toLowerCase().replace(/\s+/g, '-');
    }

    function showFields() {
      document.querySelectorAll('.field-group').forEach(el => el.classList.remove('active'));
      const val = document.getElementById('workout_type').value;
      if (val) {
        const el = document.getElementById('fields-' + toSlug(val));
        if (el) el.classList.add('active');
      }
    }

    function updateDecimal() {
      const durationInput = document.getElementById('duration');
      const span = document.getElementById('decimal-duration');
      if (!durationInput || !span) return;
      const raw = durationInput.value.trim();
      const match = raw.match(/^(\d{2}):(\d{2}):(\d{2})$/);
      if (match) {
        const h = parseInt(match[1], 10);
        const m = parseInt(match[2], 10);
        const s = parseInt(match[3], 10);
        const dec = (h * 60 + m + s / 60).toFixed(4);
        document.getElementById('decimal-value').textContent = dec;
        span.style.display = 'block';
      } else {
        span.style.display = 'none';
      }
    }

    // Show fields for the currently selected workout type on page load
    showFields();
    // Also trigger decimal preview if duration is pre-filled
    updateDecimal();
  </script>
</body>
</html>
```

**Step 3: Verify GET /edit/<id> works**

```bash
source venv/bin/activate && PORT=5001 python app.py &
# get a real id: sqlite3 workouts.db "SELECT id FROM workouts LIMIT 1;"
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5001/edit/1
# Expected: 200 (or 302 if id 1 doesn't exist)
kill %1
```

**Step 4: Commit**

```bash
git add app.py templates/edit.html
git commit -m "feat: add edit workout page"
```

---

### Task 3: Add POST /edit/<id> update route and POST /delete/<id> delete route

**Files:**
- Modify: `app.py`

**Step 1: Add the update route**

Add after `edit_workout` in `app.py`:

```python
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
            miles = float(data["miles"]) if data.get("miles") else None
            active_calories = int(data["active_calories"]) if data.get("active_calories") else None
            avg_heart_rate = int(data["avg_heart_rate"]) if data.get("avg_heart_rate") else None
        except (ValueError, KeyError):
            flash("Invalid numeric input for miles, calories, or heart rate.")
            return redirect(url_for("edit_workout", workout_id=workout_id))

        duration = data.get("duration") or None
        decimal_duration = parse_duration(duration) if duration else None

        conn.execute("""
            UPDATE workouts SET
                workout_type=?, workout_date=?, start_time=?, end_time=?,
                duration=?, decimal_duration=?, miles=?, active_calories=?, avg_heart_rate=?
            WHERE id=?
        """, (
            workout_type, workout_date,
            data.get("start_time") or None,
            data.get("end_time") or None,
            duration, decimal_duration,
            miles, active_calories, avg_heart_rate,
            workout_id,
        ))
        conn.commit()
    finally:
        conn.close()

    flash("Workout updated!")
    return redirect(url_for("index"))
```

**Step 2: Add the delete route**

Add after `update_workout` in `app.py`:

```python
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
```

**Step 3: Verify end-to-end**

```bash
source venv/bin/activate && PORT=5001 python app.py &
# 1. Visit http://127.0.0.1:5001/ — click a row
# 2. Change a field, click Update — should redirect to / with "Workout updated!" flash
# 3. Click a row again, click Delete, confirm — should redirect to / with "Workout deleted." flash
kill %1
```

**Step 4: Commit**

```bash
git add app.py
git commit -m "feat: add update and delete workout routes"
```
