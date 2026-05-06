# Decimal Duration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Compute and store a decimal minutes value from hh:mm:ss duration, and show it live next to the duration field in the form.

**Architecture:** Add a `parse_duration()` helper to app.py that converts "hh:mm:ss" to decimal minutes (h×60 + m + s/60). Store the result in a new `decimal_duration REAL` column in the workouts table. Show a live computed preview in the form via JavaScript as the user types the duration. DB migration uses ALTER TABLE inside init_db() with error handling since SQLite has no ADD COLUMN IF NOT EXISTS.

**Tech Stack:** Python 3, pytest, Flask, SQLite3, vanilla JS

---

### Task 1: Tests and parse_duration helper

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_parse_duration.py`
- Modify: `app.py` (add `parse_duration` function)

**Step 1: Install pytest**

```bash
cd /Users/jtr/Projects/workout-tracker
source venv/bin/activate
pip install pytest
pip freeze > requirements.txt
```

**Step 2: Create tests directory**

```bash
mkdir -p tests
touch tests/__init__.py
```

**Step 3: Write failing tests**

Create `tests/test_parse_duration.py`:

```python
import pytest
from app import parse_duration

def test_minutes_and_seconds():
    assert abs(parse_duration("00:59:07") - (59 + 7/60)) < 0.0001

def test_hours_minutes_seconds():
    assert abs(parse_duration("01:23:43") - (83 + 43/60)) < 0.0001

def test_zero_duration():
    assert parse_duration("00:00:00") == 0.0

def test_whole_minutes():
    assert parse_duration("00:30:00") == 30.0

def test_exactly_one_hour():
    assert parse_duration("01:00:00") == 60.0

def test_invalid_returns_none():
    assert parse_duration("") is None
    assert parse_duration("abc") is None
    assert parse_duration(None) is None
```

**Step 4: Run tests to verify they fail**

```bash
source venv/bin/activate
pytest tests/test_parse_duration.py -v
```

Expected: all 6 tests FAIL with `ImportError: cannot import name 'parse_duration'`

**Step 5: Add parse_duration to app.py**

Add this function after the imports and before `WORKOUT_TYPES` in `app.py`:

```python
def parse_duration(s):
    if not s:
        return None
    try:
        parts = s.strip().split(":")
        if len(parts) != 3:
            return None
        h, m, sec = int(parts[0]), int(parts[1]), int(parts[2])
        return h * 60 + m + sec / 60
    except (ValueError, AttributeError):
        return None
```

**Step 6: Run tests to verify they pass**

```bash
pytest tests/test_parse_duration.py -v
```

Expected: all 6 tests PASS

**Step 7: Commit**

```bash
git add tests/ app.py requirements.txt
git commit -m "feat: add parse_duration helper with tests"
```

---

### Task 2: DB migration and store decimal_duration on save

**Files:**
- Modify: `database.py` (add column to schema + ALTER TABLE migration)
- Modify: `app.py` (compute and insert decimal_duration)

**Step 1: Update database.py**

In `init_db()`, add `decimal_duration REAL` to the CREATE TABLE statement, and add an ALTER TABLE migration after it:

The full updated `init_db()`:

```python
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
```

**Step 2: Update log_workout in app.py to compute and store decimal_duration**

In the `log_workout` route, after parsing `duration`, compute:

```python
duration = data.get("duration") or None
decimal_duration = parse_duration(duration) if duration else None
```

Update the INSERT to include `decimal_duration`:

```python
conn.execute("""
    INSERT INTO workouts
        (workout_type, workout_date, start_time, end_time, duration, decimal_duration,
         miles, active_calories, avg_heart_rate)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    workout_type,
    workout_date,
    data.get("start_time") or None,
    data.get("end_time") or None,
    duration,
    decimal_duration,
    miles,
    active_calories,
    avg_heart_rate,
))
```

**Step 3: Verify migration and save work**

```bash
source venv/bin/activate
python app.py &
sleep 2
curl -s -X POST http://127.0.0.1:5000/log \
  -d "workout_type=Indoor Air Bike" \
  -d "workout_date=2026-04-17" \
  -d "miles=6.00" \
  -d "duration=00:20:05" \
  -d "active_calories=144" \
  -d "avg_heart_rate=108" \
  -d "start_time=12:35" \
  -d "end_time=12:55"
kill %1
sqlite3 workouts.db "SELECT duration, decimal_duration FROM workouts ORDER BY id DESC LIMIT 1;"
```

Expected output: `00:20:05|20.083333333333332`

(00:20:05 = 0×60 + 20 + 5/60 = 20.0833...)

**Step 4: Run all tests**

```bash
pytest tests/ -v
```

Expected: all tests PASS

**Step 5: Commit**

```bash
git add database.py app.py
git commit -m "feat: store decimal_duration on workout save"
```

---

### Task 3: Live decimal preview in the form

**Files:**
- Modify: `templates/index.html`

**Step 1: Add a read-only decimal display span next to the duration input**

In `templates/index.html`, find the duration label block:

```html
<label>Workout Duration (hh:mm:ss)
  <input type="text" name="duration" placeholder="00:20:05" pattern="\d{2}:\d{2}:\d{2}">
</label>
```

Replace it with:

```html
<label>Workout Duration (hh:mm:ss)
  <input type="text" name="duration" id="duration" placeholder="00:20:05" pattern="\d{2}:\d{2}:\d{2}" oninput="updateDecimal()">
  <span id="decimal-duration" style="display:none; font-size:0.85rem; color:#555; margin-top:4px; display:block;">
    Decimal minutes: <strong id="decimal-value"></strong>
  </span>
</label>
```

**Step 2: Add updateDecimal() to the script block**

Add this function in the `<script>` block, after `showFields()`:

```js
function updateDecimal() {
  const raw = document.getElementById('duration').value.trim();
  const span = document.getElementById('decimal-duration');
  const match = raw.match(/^(\d{2}):(\d{2}):(\d{2})$/);
  if (match) {
    const h = parseInt(match[1]);
    const m = parseInt(match[2]);
    const s = parseInt(match[3]);
    const dec = (h * 60 + m + s / 60).toFixed(4);
    document.getElementById('decimal-value').textContent = dec;
    span.style.display = 'block';
  } else {
    span.style.display = 'none';
  }
}
```

**Step 3: Verify visually**

```bash
source venv/bin/activate
python app.py
```

Open http://127.0.0.1:5000, select "Indoor Air Bike", type `00:59:07` in the duration field. The span should show `Decimal minutes: 59.1167`. Type `01:23:43` — should show `83.7167`.

**Step 4: Commit**

```bash
git add templates/index.html
git commit -m "feat: show live decimal duration preview in form"
```
