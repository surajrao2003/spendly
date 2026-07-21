# Spec: Add Expense

## Overview
This feature implements the "Add Expense" flow, replacing the `GET /expenses/add` stub with a real form-backed route. Logged-in users can record a new expense (amount, category, date, optional description) against their account. This is the first of the three CRUD steps for expenses (add/edit/delete) and the first route that writes to the `expenses` table outside of seed data — it establishes the insert pattern, validation rules, and form conventions that Steps 8 (edit) and 9 (delete) will reuse.

## Depends on
- Step 1 (Database setup) — `expenses` table and `CATEGORIES` list in `database/db.py`
- Step 3 (Login/Logout) — `session["user_id"]` for scoping the new expense to the logged-in user
- Step 5/6 (Profile page + date filter) — the profile page is the natural place to link back to after a successful add, and shares the flash-message pattern from `base.html`

## Routes
- `GET /expenses/add` — render the add-expense form, pre-filled with today's date — logged-in only
- `POST /expenses/add` — validate and insert the new expense, then redirect to `/profile` — logged-in only

Both methods are handled by the same `add_expense` view (`methods=["GET", "POST"]`), matching the existing `register`/`login` pattern in `app.py`.

## Database changes
No database changes. The `expenses` table (`database/db.py`) already has every column this feature needs: `user_id`, `amount`, `category`, `date`, `description`. No new tables, columns, or constraints.

## Templates
- **Create:** `templates/expenses_add.html` — form with fields for amount, category (`<select>` populated from `CATEGORIES`), date (defaulting to today), and optional description. Extends `base.html`. Renders inline validation errors the same way `register.html`/`login.html` do (an `error` variable passed to the template).
- **Modify:** none required. `base.html`'s nav already links to `/profile`; no new nav entry is in scope for this step (expenses are added *from* the profile page, not from top-level nav, matching the current design where profile is the hub).

## Files to change
- `app.py` — replace the `add_expense` stub with the real `GET`/`POST` implementation; add a `_parse_amount` helper (or equivalent) for validating the amount field
- `database/db.py` — add an `add_expense(user_id, amount, category, date, description)` helper (general-purpose write, belongs in `db.py` alongside `create_user`, not in `queries.py` which is profile-page-read-only)
- `CLAUDE.md` — update the route table (`GET /expenses/add` → `POST /expenses/add` implemented) and the "Features implemented so far" list once the step is done

## Files to create
- `templates/expenses_add.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders) — no f-strings in SQL, per CLAUDE.md
- Passwords hashed with werkzeug — n/a to this feature, no password handling here
- Use CSS variables — never hardcode hex values in any new styles
- All templates extend `base.html`
- `category` must be validated against the fixed `CATEGORIES` list in `database/db.py` — reject/flag anything else, never trust the raw form value
- `amount` must be validated server-side as a positive number (reject zero, negative, non-numeric, and missing values) before insert
- `date` must be validated as a well-formed ISO `YYYY-MM-DD` string, reusing the existing `_parse_iso_date` helper in `app.py` — invalid dates re-render the form with an error, they do not silently fall back (unlike the profile page's date filter, this is a write path and must not silently substitute a wrong date)
- The route must redirect unauthenticated requests to `/login`, matching every other logged-in-only route
- The new expense must always be inserted with `user_id = session["user_id"]` — never take `user_id` from form data
- DB logic (the insert) lives in `database/db.py`, never inline in `app.py`
- On successful insert, redirect to `/profile` (not re-render the add form) to avoid duplicate submissions on refresh

## Definition of done
- [ ] Visiting `/expenses/add` while logged out redirects to `/login`
- [ ] Visiting `/expenses/add` while logged in renders a form with amount, category dropdown (all 7 categories from `CATEGORIES`), date (pre-filled with today), and description fields
- [ ] Submitting the form with valid data inserts a new row into `expenses` scoped to the logged-in user's `id`, then redirects to `/profile`
- [ ] The newly added expense appears in the profile page's Recent Transactions list and is reflected in Summary and Category Breakdown totals
- [ ] Submitting with a missing/zero/negative/non-numeric amount re-renders the form with a validation error and does not insert a row
- [ ] Submitting with a category not in `CATEGORIES` re-renders the form with a validation error and does not insert a row
- [ ] Submitting with a malformed or missing date re-renders the form with a validation error and does not insert a row
- [ ] Submitting with no description succeeds (description is optional) and the profile page renders the category as the fallback label, matching existing `expense["description"] or expense["category"]` behavior
- [ ] `CLAUDE.md`'s route table and "Implemented vs stub routes" section are updated to reflect `GET/POST /expenses/add` as implemented
