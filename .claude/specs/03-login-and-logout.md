# Spec: Login And Logout

## Overview
This step lets a registered user actually authenticate. `GET /login` currently renders `login.html` with no handler for the submission, and `/logout` is a raw-string stub. This step adds session-based authentication: `POST /login` verifies credentials and establishes a logged-in session, and `GET /logout` clears it. Flask's built-in `session` (signed client-side cookie) is introduced here for the first time — no session mechanism exists anywhere in the app yet — since every future authenticated route (profile, expenses) depends on knowing who's logged in.

## Depends on
- Step 01 — Database setup (`users` table, `get_db()`). Complete.
- Step 02 — Registration (`get_user_by_email()`, so a user account exists to log into). Complete.

## Routes
- `POST /login` — verify email + password, establish session, redirect on success — public
- `GET /logout` — clear the session, redirect to landing page — logged-in (safe to also allow when logged out; it just becomes a no-op redirect)

`GET /login` already exists and is unchanged.

## Database changes
No database changes. The existing `users` table (`email`, `password_hash`) already supports credential lookup via `get_user_by_email()` from Step 02.

## Templates
- **Create:** none
- **Modify:** `templates/login.html` — change the form's `action="/login"` to `action="{{ url_for('login') }}"` (CLAUDE.md forbids hardcoded URLs); no structural changes needed since `error` display is already wired up

## Files to change
- `app.py` — change `login` view to accept `GET` and `POST`; replace the `/logout` stub with a real handler; set `app.secret_key` (required for Flask sessions to sign the cookie)
- `templates/login.html` — fix hardcoded form action to use `url_for()`

## Files to create
None.

## New dependencies
No new dependencies. Flask's `session` object is part of Flask itself (already a dependency).

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — no string formatting in SQL
- Passwords hashed with werkzeug — verify via `check_password_hash`, never compare plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Never reveal via the error message whether the failure was a bad email vs. a bad password (use one generic message, e.g. "Invalid email or password.") — avoids leaking which emails are registered
- `app.secret_key` must come from an environment variable or a fixed dev-only value, clearly flagged as needing a real secret in production — do not commit a production secret
- Session must store only the minimum needed to identify the user (e.g. `session["user_id"]`), never the password or password hash
- `/logout` must clear the session (`session.clear()` or `session.pop("user_id", None)`), not just redirect

## Definition of done
- [ ] Visiting `/login` still renders the form (GET unchanged)
- [ ] Submitting valid credentials for an existing user redirects (not re-renders) and sets a session cookie (inspect via browser devtools → Application → Cookies, or `curl -i` for a `Set-Cookie` header)
- [ ] Submitting a non-existent email re-renders `login.html` with a generic "Invalid email or password." error, no 500
- [ ] Submitting a wrong password for a real email re-renders `login.html` with the same generic error message (indistinguishable from the non-existent-email case)
- [ ] Submitting with a missing/empty field re-renders the form with an error instead of a 500 or a raw string response
- [ ] Visiting `/logout` after logging in clears the session (a subsequent request no longer carries `session["user_id"]`) and redirects to the landing page
- [ ] Visiting `/logout` while not logged in does not error — it redirects cleanly
- [ ] `login.html`'s form no longer hardcodes `/login` — it uses `url_for('login')`
- [ ] No new pip packages were added to `requirements.txt`
- [ ] App still starts cleanly on port 5001 with no errors
