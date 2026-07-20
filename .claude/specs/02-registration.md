# Spec: Registration

## Overview
This step implements account creation for Spendly. The `GET /register` route already renders `register.html` with a form that posts to `/register`, but there is no handler for the submission — no validation, no password hashing, no user row is created. This step adds the `POST /register` handler so a visitor can actually create an account, laying the foundation for login (a later step) and all authenticated features that follow.

## Depends on
- Step 01 — Database setup (`users` table, `get_db()`, `init_db()`) must be complete. It is.

## Routes
- `POST /register` — accept the registration form, validate input, create the user, redirect on success — public

`GET /register` already exists and is unchanged.

## Database changes
No database changes. The existing `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) already supports registration as-is.

## Templates
- **Create:** none
- **Modify:** `templates/register.html` — change the form's `action="/register"` to `action="{{ url_for('register') }}"` (CLAUDE.md forbids hardcoded URLs); no structural changes needed since `error` display is already wired up

## Files to change
- `app.py` — change `register` view to accept `GET` and `POST`, add form handling logic
- `database/db.py` — add a function (e.g. `create_user(name, email, password_hash)`) so `app.py` never runs SQL directly
- `templates/register.html` — fix hardcoded form action to use `url_for()`

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — no string formatting in SQL
- Passwords hashed with werkzeug (`generate_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Duplicate email must be rejected with a clear error re-rendered on the same form (re-use the existing `error` block in `register.html`)
- Validate required fields server-side even though the form has `required` attributes (client-side validation is not a security boundary)
- On success, redirect (e.g. to `/login`) rather than rendering a template directly from the POST handler, to avoid resubmission on refresh

## Definition of done
- [ ] Visiting `/register` still renders the form (GET unchanged)
- [ ] Submitting the form with valid, unique name/email/password creates a new row in `users` with a hashed password (verify via sqlite3 CLI or a quick script — plaintext password must never appear in the DB)
- [ ] Submitting with an email that already exists re-renders `register.html` with an error message and does not create a duplicate row
- [ ] Submitting with a missing/empty field re-renders the form with an error instead of a 500 or a raw string response
- [ ] After successful registration, the browser is redirected (not just re-rendered) to a next page (e.g. `/login`)
- [ ] `register.html`'s form no longer hardcodes `/register` — it uses `url_for('register')`
- [ ] No new pip packages were added to `requirements.txt`
- [ ] App still starts cleanly on port 5001 with no errors
