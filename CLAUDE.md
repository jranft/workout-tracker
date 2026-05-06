# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A local Flask + SQLite workout tracker. The user logs workouts via a web form; each workout type has different data fields. The app will eventually be deployed online.

## Commands

```bash
# Activate the virtualenv first (always required)
source venv/bin/activate

# Run the app
python app.py
# → http://127.0.0.1:5000

# Run all tests
pytest tests/ -v

# Run a single test
pytest tests/test_parse_duration.py::test_minutes_and_seconds -v

# Inspect the database
sqlite3 workouts.db "SELECT * FROM workouts ORDER BY id DESC LIMIT 5;"
```

Set `SECRET_KEY` env var before any public deployment.

## Architecture

**`app.py`** — Flask app, routes, and `parse_duration()`.
- `WORKOUT_TYPES` list controls the dropdown. Add new types here.
- `parse_duration(s)` converts `"hh:mm:ss"` → decimal minutes (`h*60 + m + s/60`). Returns `None` for invalid input. The JS in `index.html` mirrors this formula exactly — keep them in sync.
- `init_db()` is called at module level so it runs under both `python app.py` and WSGI servers.

**`database.py`** — SQLite helpers (`get_db`, `init_db`).
- DB file is at an absolute path relative to this file, not the process cwd.
- `init_db()` runs `CREATE TABLE IF NOT EXISTS` then an `ALTER TABLE` migration for columns added after initial deployment. When adding a new column, add it to both the `CREATE TABLE` statement and a new `ALTER TABLE` block (catch only `sqlite3.OperationalError` with `"duplicate column"` in the message).

**`templates/index.html`** — Single Jinja2 template, inline CSS and JS.
- Workout-type-specific fields live in `<div class="field-group" id="fields-<slug>">` divs. `showFields()` derives the slug from the selected option value via `toSlug()` (lowercase + hyphens), so the div id must match. When adding a new workout type, add a `<div class="field-group" id="fields-<slug-of-type-name>">` block with its fields.
- `decimal_duration` is shown as a live preview via `updateDecimal()` — fires on every keystroke of the duration field.

## Adding a new workout type

1. Add the name to `WORKOUT_TYPES` in `app.py`.
2. Add a `<div class="field-group" id="fields-<slug>">` block in `templates/index.html` with the type-specific inputs.
3. Add any new fields to the `workouts` table in `database.py` (both `CREATE TABLE` and an `ALTER TABLE` migration).
4. Update the `INSERT` in `log_workout()` in `app.py` to include the new fields.

## Database schema

Single table `workouts`. All fields except `workout_type` and `workout_date` are nullable to support multiple workout types in one table:

| column | type | notes |
|---|---|---|
| workout_type | TEXT | e.g. "Indoor Air Bike" |
| workout_date | TEXT | YYYY-MM-DD |
| start_time / end_time | TEXT | HH:MM (from `<input type="time">`) |
| duration | TEXT | hh:mm:ss raw string |
| decimal_duration | REAL | computed by parse_duration() |
| miles | REAL | |
| active_calories | INTEGER | |
| avg_heart_rate | INTEGER | |
