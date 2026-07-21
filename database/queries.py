"""
Profile-page query helpers for Spendly.

This module holds SQLite access specific to the /profile route —
transaction history, summary stats, and category breakdown — kept
separate from the general-purpose helpers in database/db.py. As with
db.py, route functions in app.py should fetch data via these helpers
and never execute SQL directly (see CLAUDE.md).
"""

from database.db import get_db


# ------------------------------------------------------------------ #
# Transaction history                                                  #
# ------------------------------------------------------------------ #
def get_recent_transactions(user_id, limit=10):
    """Return `user_id`'s most recent expenses, newest first, capped at `limit`."""
    db = get_db()
    try:
        return db.execute(
            """
            SELECT id, amount, category, date, description
            FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    finally:
        db.close()


# ------------------------------------------------------------------ #
# Category breakdown                                                   #
# ------------------------------------------------------------------ #
def get_category_breakdown(user_id):
    """Return per-category totals and percentage share of total spending for user_id."""
    db = get_db()
    try:
        rows = db.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY total DESC
            """,
            (user_id,),
        ).fetchall()
    finally:
        db.close()

    if not rows:
        return []

    grand_total = sum(row["total"] for row in rows)

    breakdown = []
    for row in rows:
        pct = int(round((row["total"] / grand_total) * 100)) if grand_total else 0
        breakdown.append({"name": row["category"], "amount": row["total"], "pct": pct})

    # Normalize rounding so percentages sum to exactly 100 — adjust the
    # largest category (first row, since rows are ordered by total DESC).
    remainder = 100 - sum(item["pct"] for item in breakdown)
    if remainder != 0:
        breakdown[0]["pct"] += remainder

    return breakdown


# ------------------------------------------------------------------ #
# Summary stats                                                        #
# ------------------------------------------------------------------ #
def get_summary_stats(user_id):
    """Return total spent, transaction count, and top category for user_id."""
    db = get_db()
    try:
        totals = db.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_spent,
                   COUNT(*) AS transaction_count
            FROM expenses
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        top = db.execute(
            """
            SELECT category
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

        return {
            "total_spent": totals["total_spent"],
            "transaction_count": totals["transaction_count"],
            "top_category": top["category"] if top else "—",
        }
    finally:
        db.close()
