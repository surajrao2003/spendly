import os
from datetime import date, datetime, timedelta

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import (
    create_user,
    get_db,
    get_user_by_email,
    get_user_by_id,
    init_db,
    seed_db,
)
from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
)

app = Flask(__name__)

# Dev-only fallback. In production, SECRET_KEY MUST be set via environment
# variable — never commit a real secret to source control.
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-insecure-secret-key")

with app.app_context():
    init_db()
    seed_db()


@app.context_processor
def inject_logged_in():
    return {"logged_in": "user_id" in session}


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("landing"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.")

        if get_user_by_email(email) is not None:
            return render_template(
                "register.html", error="An account with this email already exists."
            )

        password_hash = generate_password_hash(password)
        create_user(name, email, password_hash)
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("profile"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template(
                "login.html", error="Please enter both your email and password."
            )

        user = get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")

        session.clear()
        session["user_id"] = user["id"]
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/analytics")
def analytics():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("analytics.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("landing"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


def _parse_iso_date(value):
    """Return `value` unchanged if it's a well-formed ISO `YYYY-MM-DD` date, else None."""
    if not value:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
    return value


def _date_presets():
    """Return the (start, end) ISO date pairs for the profile page's quick-select presets."""
    today = date.today()
    return {
        "this_month": (today.replace(day=1).isoformat(), today.isoformat()),
        "last_3_months": ((today - timedelta(days=90)).isoformat(), today.isoformat()),
        "last_6_months": ((today - timedelta(days=180)).isoformat(), today.isoformat()),
    }


def _resolve_date_filter(args):
    """Parse and validate `date_from`/`date_to` from request args.

    Falls back to `(None, None)` — no filter — if either value is missing or
    malformed, or if `date_from` is after `date_to` (flashing an error in the
    latter case).
    """
    date_from = _parse_iso_date(args.get("date_from"))
    date_to = _parse_iso_date(args.get("date_to"))

    if date_from and date_to and date_from > date_to:
        flash("Start date must be before end date.")
        return None, None

    return date_from, date_to


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])
    if user is None:
        session.clear()
        return redirect(url_for("login"))

    date_from, date_to = _resolve_date_filter(request.args)

    # --- transaction history (Subagent 1) ---
    expenses = get_recent_transactions(user["id"], date_from=date_from, date_to=date_to)

    # --- summary stats (Subagent 2) ---
    stats = get_summary_stats(user["id"], date_from=date_from, date_to=date_to)

    # --- category breakdown (Subagent 3) ---
    breakdown = get_category_breakdown(user["id"], date_from=date_from, date_to=date_to)

    return render_template(
        "profile.html",
        user=user,
        expenses=expenses,
        stats=stats,
        breakdown=breakdown,
        date_from=date_from,
        date_to=date_to,
        presets=_date_presets(),
    )


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
