"""
Database helpers for Spendly.

All SQLite access for the application must go through this module —
route functions in app.py should fetch data via these helpers and
never execute SQL directly (see CLAUDE.md).
"""

import os
import sqlite3
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

# ------------------------------------------------------------------ #
# Path resolution                                                     #
# ------------------------------------------------------------------ #
# Resolve the DB path relative to this file's location (not the
# process's current working directory) so behavior is identical
# whether the app is launched via `python app.py`, from another cwd,
# or imported by pytest.
_DATABASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_DATABASE_DIR)
DB_PATH = os.path.join(_PROJECT_ROOT, "expense_tracker.db")

# Fixed category list — used by seed data today, and by the
# expense form / filters in later steps.
CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]


# ------------------------------------------------------------------ #
# Connection handling                                                 #
# ------------------------------------------------------------------ #
def get_db():
    """
    Open and return a new SQLite connection to the Spendly database.

    Every connection returned here has:
      - row_factory = sqlite3.Row, so columns can be accessed by name
        (e.g. row["email"]) as well as by index
      - foreign key enforcement turned ON (SQLite disables this by
        default, per-connection, so it must be set every time)

    The caller owns the returned connection and is responsible for
    closing it when done, e.g.:
        db = get_db()
        try:
            ...
            db.commit()
        finally:
            db.close()
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ------------------------------------------------------------------ #
# Schema                                                               #
# ------------------------------------------------------------------ #
def init_db():
    """Create all tables if they don't already exist. Safe to call repeatedly."""
    db = get_db()
    try:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                amount      REAL NOT NULL,
                category    TEXT NOT NULL,
                date        TEXT NOT NULL,
                description TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        db.commit()
    finally:
        db.close()


# ------------------------------------------------------------------ #
# Seed data                                                            #
# ------------------------------------------------------------------ #
def seed_db():
    """
    Insert demo data for local development, exactly once.

    If the `users` table already has any rows, this is a no-op — safe
    to call unconditionally on every app startup without duplicating
    records.
    """
    db = get_db()
    try:
        already_seeded = db.execute("SELECT 1 FROM users LIMIT 1").fetchone()
        if already_seeded is not None:
            return

        password_hash = generate_password_hash("demo123")
        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", password_hash),
        )
        user_id = cursor.lastrowid

        today = date.today()
        first_of_month = today.replace(day=1)

        def expense_date(days_before_today):
            """
            ISO date `days_before_today` days before today, clamped so it
            never falls before the 1st of the current month. Counting
            backward from "today" guarantees every seeded date is <= today
            regardless of what day of the month it happens to be when
            seed_db() actually runs.
            """
            d = today - timedelta(days=days_before_today)
            return max(d, first_of_month).isoformat()

        # 8 expenses covering all 7 fixed categories (Food appears twice).
        sample_expenses = [
            (user_id, 42.50, "Food", expense_date(17), "Groceries"),
            (user_id, 89.99, "Shopping", expense_date(14), "New running shoes"),
            (user_id, 32.00, "Transport", expense_date(12), "Fuel top-up"),
            (user_id, 120.00, "Bills", expense_date(9), "Electricity bill"),
            (user_id, 15.75, "Food", expense_date(7), "Lunch with coworkers"),
            (user_id, 60.00, "Health", expense_date(5), "Pharmacy purchase"),
            (user_id, 25.00, "Entertainment", expense_date(2), "Movie tickets"),
            (user_id, 18.30, "Other", expense_date(0), "Miscellaneous"),
        ]

        db.executemany(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            sample_expenses,
        )
        db.commit()
    finally:
        db.close()
