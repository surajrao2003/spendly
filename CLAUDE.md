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
| `GET/POST /expenses/add` | Implemented — renders `expenses_add.html` with an amount/category/date/description form (logged-in only). Validates amount (positive number via `_parse_amount`), category (must be in `CATEGORIES`), and date (`_parse_iso_date`) server-side; any failure re-renders the form with an inline error and the user's resubmitted values, it does not silently fall back. On success inserts via `database/db.py`'s `add_expense()` scoped to `session["user_id"]` and redirects to `/profile`. |
| `GET/POST /expenses/<id>/edit` | Implemented — renders `expenses_edit.html` pre-filled with an existing expense's amount/category/date/description (logged-in only, must own the expense — returns 404 otherwise). Same server-side validation as `/expenses/add` (`_parse_amount`, `CATEGORIES`, `_parse_iso_date`); any failure re-renders the form with an inline error, it does not silently fall back. On success updates via `database/db.py`'s `update_expense()` scoped to `session["user_id"]` and redirects to `/profile`. |
| `GET/POST /expenses/<id>/delete` | Implemented — `GET` renders `expenses_delete.html` with a read-only preview of the expense's amount/category/date/description and a confirmation form (logged-in only, must own the expense — 404 otherwise). `POST` deletes it via `database/db.py`'s `delete_expense()` scoped to `session["user_id"]`, flashes a confirmation message, and redirects to `/profile`. Deletion never happens on `GET`. |

**Do not implement a stub route unless the active task explicitly targets that step.**

---

## Features implemented so far

- **Step 1 — Database setup**: `database/db.py` provides `get_db()` (opens a SQLite connection with `row_factory = sqlite3.Row` and FK enforcement on), `init_db()` (creates `users` and `expenses` tables), and `seed_db()` (idempotent — inserts one demo user, `demo@spendly.com` / `demo123`, plus 8 sample expenses across all 7 fixed categories).
- **Step 2 — Registration**: `GET/POST /register` creates a new user with a werkzeug-hashed password.
- **Step 3 — Login/Logout**: `GET/POST /login` authenticates and sets `session["user_id"]`; `GET /logout` clears the session.
- **Step 4 — Profile page UI**: static template with four cards — user info, summary stats, recent transactions, category breakdown.
- **Step 5 — Profile page backend routes**: `database/queries.py` wires the four profile-page cards to live data via `get_user_by_id`, `get_summary_stats`, `get_recent_transactions`, `get_category_breakdown`. All currency values render with the ₹ symbol.
- **Step 6 — Date filter for profile page**: optional `date_from`/`date_to` query params on `GET /profile`, validated in `app.py` (`_parse_iso_date`, `_resolve_date_filter`, `_date_presets`) and threaded through all three query helpers in `database/queries.py` via a shared `_date_where()` clause builder. Adds a filter bar to `templates/profile.html` (styled in `static/css/profile.css`) and basic flash-message support in `templates/base.html`.

- **Step 7 — Add expense**: `GET/POST /expenses/add` (logged-in only) renders a form for amount/category/date/description. `app.py` adds `_parse_amount()` alongside the existing `_parse_iso_date()` for server-side validation; unlike the profile page's date filter, invalid input here re-renders the form with a visible error (never a silent fallback), since this is a write path. `database/db.py` adds `add_expense(user_id, amount, category, date, description)`, mirroring `create_user`'s open/insert/commit/close-in-finally shape. Empty descriptions are stored as `NULL`. New template `templates/expenses_add.html` reuses the `auth-*`/`form-*` CSS classes from `register.html` — no new stylesheet.

- **Step 8 — Edit expense**: `GET/POST /expenses/<id>/edit` (logged-in only) mirrors Step 7's form and validation, applied to an `UPDATE` instead of an `INSERT`. `database/db.py` adds `get_expense_by_id(expense_id, user_id)` (scoped `SELECT`, doubles as the ownership check) and `update_expense(expense_id, user_id, amount, category, date, description)` (scoped `UPDATE`); the route calls `abort(404)` if `get_expense_by_id` returns `None`, so a missing expense and one owned by another user are indistinguishable to the client. New template `templates/expenses_edit.html` reuses `expenses_add.html`'s CSS classes. `templates/profile.html`'s Recent Transactions rows gained a `tx-edit` link to reach it; `static/css/style.css`'s `.tx-row` grid grew a 4th column and `static/css/profile.css` adds the `.tx-edit` style.

- **Step 9 — Delete expense**: `GET/POST /expenses/<id>/delete` (logged-in only) reuses Step 8's `get_expense_by_id(id, user_id)` for the same ownership-scoped lookup/404 check. `GET` renders `templates/expenses_delete.html`, a read-only confirmation page (no form fields, just the expense's details) with a `POST` form to confirm. `database/db.py` adds `delete_expense(expense_id, user_id)` (scoped `DELETE`, mirroring `update_expense`'s shape); since its natural name collides with the `app.py` view function, it's imported as `delete_expense as db_delete_expense`. On success it flashes "Expense deleted." and redirects to `/profile`. `templates/profile.html`'s Recent Transactions rows gained a `tx-actions` wrapper around the `tx-edit` and new `tx-delete` links; `static/css/style.css`'s `.tx-row`/`.tx-header` grids widened their last column to fit both, and `static/css/profile.css` adds the `.tx-delete` style (hover uses the existing `--danger` variable).

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
- **When a `database/db.py` write-helper's natural name collides with an existing `app.py` view function name** (e.g. `add_expense`), import the helper under an alias (`add_expense as db_add_expense`) — never rename the view function, since its name is the Flask endpoint used by `url_for()`
- The app runs on **port 5001**, not the Flask default 5000 — don't change this