# Spec: Delete Expense

## Overview
This feature replaces the stub `GET /expenses/<id>/delete` route with a real deletion flow. It lets a logged-in user permanently remove one of their own expenses, closing out the last of the three core write operations (add, edit, delete) that Spendly supports on the `expenses` table. Since deletion is destructive and irreversible, it requires an explicit confirmation step rather than deleting on a single GET request.

## Depends on
- Step 1 (Database setup) — `expenses` table, `get_db()`
- Step 5/6 (Profile page + date filter) — `/profile` is the redirect target and the page expenses link from
- Step 8 (Edit expense) — `get_expense_by_id()` already provides the ownership-scoped lookup this feature reuses; `templates/profile.html`'s `tx-row` already has a 4-column layout to extend

## Routes
- `GET /expenses/<int:id>/delete` — renders a confirmation page showing the expense's details, with a form that POSTs to the same URL to confirm deletion — logged-in only, must own the expense (404 otherwise)
- `POST /expenses/<int:id>/delete` — deletes the expense, flashes a success message, redirects to `/profile` — logged-in only, must own the expense (404 otherwise)

## Database changes
No database changes. `database/db.py` already has the `expenses` table and `get_expense_by_id(expense_id, user_id)` for the ownership-scoped lookup. A new `delete_expense(expense_id, user_id)` helper is needed (scoped `DELETE`, mirroring `update_expense`'s shape).

## Templates
- **Create:** `templates/expenses_delete.html` — confirmation page showing amount, category, date, description, with a "Delete" button (POST form) and a "Cancel" link back to `/profile`. Reuses `auth-*`/`form-*` CSS classes from `expenses_add.html`/`expenses_edit.html` — no new stylesheet.
- **Modify:** `templates/profile.html` — add a `tx-delete` link/button next to the existing `tx-edit` link in each Recent Transactions row, pointing to `url_for('delete_expense', id=expense['id'])`.

## Files to change
- `app.py` — replace the stub `delete_expense` view with `GET`/`POST` handling, session check, ownership check via `get_expense_by_id`, and a call to the new `db.py` delete helper
- `database/db.py` — add `delete_expense(expense_id, user_id)`
- `templates/profile.html` — add the `tx-delete` link in each transaction row
- `static/css/profile.css` — add a `.tx-delete` style (mirroring `.tx-edit`)
- `CLAUDE.md` — update the routes table and "Features implemented so far" once this step is done (do this as part of implementation, not part of this spec)

## Files to create
- `templates/expenses_delete.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — `?` placeholders, no f-strings in SQL
- Passwords hashed with werkzeug (n/a to this feature, but never regress existing auth code)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `abort(404)` for a missing/not-owned expense — never a bare error string
- `GET` must only render the confirmation page; the actual delete must only happen on `POST`
- Reuse `get_expense_by_id` for the ownership check exactly as Step 8 does — don't duplicate that query inline in `app.py`
- Follow the existing `add_expense`/`update_expense` naming precedent: if `delete_expense` collides with the `app.py` view function name, import the DB helper under an alias (`delete_expense as db_delete_expense`)

## Definition of done
- [ ] Visiting `/expenses/<id>/delete` for an expense you own (logged in) shows a confirmation page with that expense's amount, category, date, and description
- [ ] Visiting `/expenses/<id>/delete` for an expense that doesn't exist, or belongs to another user, returns a 404
- [ ] Visiting `/expenses/<id>/delete` while logged out redirects to `/login`
- [ ] Submitting the confirmation form (POST) deletes the expense from the database and redirects to `/profile`
- [ ] After deletion, the expense no longer appears in Recent Transactions, and summary stats / category breakdown on `/profile` reflect its removal
- [ ] Clicking "Cancel" on the confirmation page returns to `/profile` without deleting anything
- [ ] The Recent Transactions row on `/profile` has a working delete link/button alongside the existing edit link
