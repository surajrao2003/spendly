# CLAUDE.md

## Project overview

Spendly is a lightweight personal expense tracker built with Flask and SQLite.

---

## Architecture
```
spendly/
├── app.py              # All routes — single file, no blueprints
├── database/
│   ├── db.py            # Core SQLite helpers: get_db(), init_db(), seed_db(), user queries
│   └── queries.py        # Profile-page query helpers: summary stats, recent transactions, category breakdown
├── templates/
│   ├── base.html       # Shared layout — all templates must extend this; renders flash messages
│   └── *.html          # One template per page
├── static/
│   ├── css/
│   │   ├── style.css       # Global styles
│   │   ├── landing.css     # Landing-page-only styles
│   │   └── profile.css     # Profile-page filter bar styles
│   └── js/
│       └── main.js         # Vanilla JS only
├── tests/
│   ├── conftest.py                        # Flask app/client fixtures; isolates each test on a temp SQLite DB
│   └── test_date_filter_profile_page.py   # Tests for the profile page's date-range filter
└── requirements.txt
```

**Where things belong:**
- New routes → `app.py` only, no blueprints
- General DB logic (users, connection setup) → `database/db.py`
- Profile-page query logic (stats, transactions, breakdown) → `database/queries.py`
- DB logic never lives inline in routes
- New pages → new `.html` file extending `base.html`
- Page-specific styles → new `.css` file, not inline `<style>` tags

---

## Code style

- Python: PEP 8, snake_case for all variables and functions
- Templates: Jinja2 with `url_for()` for every internal link — never hardcode URLs
- Route functions: one responsibility only — fetch data, render template, done
- DB queries: always use parameterized queries (`?` placeholders) — never f-strings in SQL
- Error handling: use `abort()` for HTTP errors, not bare `return "error string"`

---

## Tech constraints

- **Flask only** — no FastAPI, no Django, no other web frameworks
- **SQLite only** — no PostgreSQL, no SQLAlchemy ORM, no external DB
- **Vanilla JS only** — no React, no jQuery, no npm packages
- **No new pip packages** — work within `requirements.txt` as-is unless explicitly told otherwise
- Python 3.10+ assumed — f-strings and `match` statements are fine

---

## Commands
```bash
# Setup
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run dev server (port 5001)
python app.py

# Run all tests
pytest

# Run a specific test file
pytest tests/test_foo.py

# Run a specific test by name
pytest -k "test_name"

# Run tests with output visible
pytest -s
```

---

## Implemented vs stub routes

| Route | Status |
|---|---|
| `GET /` | Implemented — renders `landing.html` |
| `GET /register` | Implemented — renders `register.html` |
| `GET /login` | Implemented — renders `login.html` |
| `GET /terms` | Implemented — renders `terms.html` |
| `GET /privacy` | Implemented — renders `privacy.html` |
| `GET /logout` | Implemented — clears session, redirects to landing |
| `GET /profile` | Implemented — renders `profile.html` with live summary stats, recent transactions, and category breakdown from `database/queries.py`, all scoped to the logged-in user. Supports optional `date_from`/`date_to` query params (ISO `YYYY-MM-DD`) to filter all three sections to a date range, with quick presets (This Month / Last 3 Months / Last 6 Months / All Time) and a custom-range form. Invalid or malformed date params silently fall back to all-time data; a `date_from` after `date_to` flashes an error and falls back the same way. |
| `GET /expenses/add` | Stub — Step 7 |
| `GET /expenses/<id>/edit` | Stub — Step 8 |
| `GET /expenses/<id>/delete` | Stub — Step 9 |

**Do not implement a stub route unless the active task explicitly targets that step.**

---

## Features implemented so far

- **Step 1 — Database setup**: `database/db.py` provides `get_db()` (opens a SQLite connection with `row_factory = sqlite3.Row` and FK enforcement on), `init_db()` (creates `users` and `expenses` tables), and `seed_db()` (idempotent — inserts one demo user, `demo@spendly.com` / `demo123`, plus 8 sample expenses across all 7 fixed categories).
- **Step 2 — Registration**: `GET/POST /register` creates a new user with a werkzeug-hashed password.
- **Step 3 — Login/Logout**: `GET/POST /login` authenticates and sets `session["user_id"]`; `GET /logout` clears the session.
- **Step 4 — Profile page UI**: static template with four cards — user info, summary stats, recent transactions, category breakdown.
- **Step 5 — Profile page backend routes**: `database/queries.py` wires the four profile-page cards to live data via `get_user_by_id`, `get_summary_stats`, `get_recent_transactions`, `get_category_breakdown`. All currency values render with the ₹ symbol.
- **Step 6 — Date filter for profile page**: optional `date_from`/`date_to` query params on `GET /profile`, validated in `app.py` (`_parse_iso_date`, `_resolve_date_filter`, `_date_presets`) and threaded through all three query helpers in `database/queries.py` via a shared `_date_where()` clause builder. Adds a filter bar to `templates/profile.html` (styled in `static/css/profile.css`) and basic flash-message support in `templates/base.html`.

A `tests/` suite exists (pytest + pytest-flask) covering the Step 6 date filter, using a `conftest.py` fixture that monkeypatches `database.db.DB_PATH` to an isolated temp file per test.

---

## Warnings and things to avoid

- **Never use raw string returns for stub routes** once a step is implemented — always render a template
- **Never hardcode URLs** in templates — always use `url_for()`
- **Never put DB logic in route functions** — it belongs in `database/db.py` or `database/queries.py`
- **Never install new packages** mid-feature without flagging it — keep `requirements.txt` in sync
- **Never use JS frameworks** — the frontend is intentionally vanilla
- **FK enforcement is manual** — SQLite foreign keys are off by default; `get_db()` must run `PRAGMA foreign_keys = ON` on every connection
- **Never build SQL query text with an f-string** — even for static clause fragments; use plain string concatenation (`"..." + where + "..."`) so nothing resembles unsafe interpolation, and keep all real values in the `params` list bound via `?` placeholders
- **`database/db.py`'s `DB_PATH` points at a real on-disk file**, not `:memory:` — tests must monkeypatch `database.db.DB_PATH` to a temp file *before* importing `app` (see `tests/conftest.py`), since `app.py` calls `init_db()`/`seed_db()` at module import time
- The app runs on **port 5001**, not the Flask default 5000 — don't change this