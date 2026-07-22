# Spec: Edit Expense

## Overview
This feature implements the "Edit Expense" flow, replacing the `GET /expenses/<id>/edit` stub with a real form-backed route that lets a logged-in user update an existing expense they own (amount, category, date, description). It is the second of the three CRUD steps for expenses (add/edit/delete) and reuses the validation rules, form conventions, and template structure established in Step 7 (Add Expense), applied to an `UPDATE` instead of an `INSERT`. This step also adds the first per-transaction affordance to the profile page's Recent Transactions list, since there is currently no way to reach an individual expense's edit page.

## Depends on
- Step 1 (Database setup) — `expenses` table and `CATEGORIES` list in `database/db.py`
- Step 3 (Login/Logout) — `session["user_id"]` for authorization
- Step 5/6 (Profile page + date filter) — Recent Transactions list is where edit links are added, and the page to redirect back to after a successful edit
- Step 7 (Add Expense) — establishes `_parse_amount`/`_parse_iso_date` validation helpers and the add-expense form pattern this feature mirrors

## Routes
- `GET /expenses/<int:id>/edit` — render the edit form pre-filled with the expense's current values — logged-in only, must own the expense
- `POST /expenses/<int:id>/edit` — validate and update the expense, then redirect to `/profile` — logged-in only, must own the expense

Both methods are handled by the same `edit_expense` view (`methods=["GET", "POST"]`), matching the `add_expense` pattern in `app.py`.

Authorization rule: if the expense with `id` does not exist, or exists but belongs to a different `user_id` than `session["user_id"]`, the route responds with `abort(404)` (per CLAUDE.md's rule to use `abort()` for HTTP errors, not a bare string) — it must never reveal another user's expense data or allow editing it.

## Database changes
No new tables or columns. The `expenses` table (`database/db.py`) already has every column this feature needs: `id`, `user_id`, `amount`, `category`, `date`, `description`. This feature adds an `UPDATE` query, not a schema change.

## Templates
- **Create:** `templates/expenses_edit.html` — same field layout as `templates/expenses_add.html` (amount, category `<select>`, date, optional description), pre-filled with the expense's current values instead of empty/today defaults. Extends `base.html`. Renders inline validation errors the same way `expenses_add.html` does.
- **Modify:** `templates/profile.html` — add an "Edit" link/button to each `<li class="tx-row">` in the Recent Transactions list, pointing to `url_for('edit_expense', id=expense['id'])`. This is the only template change; no other page currently links to individual expenses.

## Files to change
- `app.py` — replace the `edit_expense` stub with the real `GET`/`POST` implementation; reuse the existing `_parse_amount` and `_parse_iso_date` helpers
- `database/db.py` — add a `get_expense_by_id(expense_id)` helper (to fetch the expense for ownership-checking and form pre-fill) and an `update_expense(expense_id, amount, category, date, description)` helper, mirroring the shape of `add_expense`
- `templates/profile.html` — add the per-transaction edit link described above
- `CLAUDE.md` — update the route table (`GET /expenses/<id>/edit` → `GET/POST /expenses/<id>/edit` implemented) and the "Features implemented so far" list once the step is done

## Files to create
- `templates/expenses_edit.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders) — no f-strings in SQL, per CLAUDE.md
- Passwords hashed with werkzeug — n/a to this feature, no password handling here
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `category` must be validated against the fixed `CATEGORIES` list in `database/db.py` — reject anything else
- `amount` must be validated server-side as a positive number (reject zero, negative, non-numeric, and missing values) before update
- `date` must be validated as a well-formed ISO `YYYY-MM-DD` string via `_parse_iso_date` — invalid input re-renders the form with a visible error, it never silently falls back (this is a write path, matching Step 7's rule, not the profile page's read-path date filter)
- The route must redirect unauthenticated requests to `/login`, matching every other logged-in-only route
- The route must `abort(404)` if the expense doesn't exist or doesn't belong to `session["user_id"]` — ownership must be checked server-side on every request, never trusted from the form
- The update must never change `user_id` — it is not an editable field and must not be accepted from form data
- DB logic (the fetch-by-id and the update) lives in `database/db.py`, never inline in `app.py`
- On successful update, redirect to `/profile` (not re-render the edit form) to avoid duplicate submissions on refresh

## Definition of done
- [ ] Visiting `/expenses/<id>/edit` while logged out redirects to `/login`
- [ ] Visiting `/expenses/<id>/edit` for an expense that doesn't exist returns a 404
- [ ] Visiting `/expenses/<id>/edit` for an expense owned by a different user returns a 404 (not the expense's data)
- [ ] Visiting `/expenses/<id>/edit` for an expense you own renders a form pre-filled with its current amount, category, date, and description
- [ ] Submitting the form with valid data updates the existing row (not a new insert) and redirects to `/profile`
- [ ] The updated values appear in the profile page's Recent Transactions list and are reflected in Summary and Category Breakdown totals
- [ ] Submitting with a missing/zero/negative/non-numeric amount re-renders the form with a validation error and does not modify the row
- [ ] Submitting with a category not in `CATEGORIES` re-renders the form with a validation error and does not modify the row
- [ ] Submitting with a malformed or missing date re-renders the form with a validation error and does not modify the row
- [ ] Submitting with no description succeeds (description is optional) and the profile page falls back to displaying the category, matching existing behavior
- [ ] The profile page's Recent Transactions list shows a working edit link/button for each transaction that navigates to that transaction's edit page
- [ ] `CLAUDE.md`'s route table and "Implemented vs stub routes" section are updated to reflect `GET/POST /expenses/<id>/edit` as implemented
