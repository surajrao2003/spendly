# Spec: Profile Page

## Overview
This step gives a logged-in user a page to view their own account details. `GET /profile` currently exists only as a raw-string stub (`"Profile page — coming in Step 4"`), and there is no way to reach it from the UI at all — `base.html`'s nav only ever links to sign-in/register or sign-out. This step turns `/profile` into a real, protected page rendering the user's name, email, and member-since date, and adds the nav link so a logged-in user can actually get there. It is read-only: editing account details and expense management are out of scope and land in later steps.

## Depends on
- Step 01 — Database setup (`users` table, `get_db()`). Complete.
- Step 03 — Login and Logout (`session["user_id"]`, so there is a logged-in user to look up). Complete.

## Routes
- `GET /profile` — fetch the logged-in user's own record and render it — logged-in only (redirect to `/login` if `session["user_id"]` is absent)

## Database changes
No database changes. The existing `users` table (`id`, `name`, `email`, `created_at`) already holds everything this page displays. `get_user_by_email()` exists but nothing currently fetches a user by `id` — that lookup needs to be added.

## Templates
- **Create:** `templates/profile.html` — displays name, email, and member-since date (formatted from `created_at`); extends `base.html`
- **Modify:** `templates/base.html` — add a "Profile" link inside the existing `{% if logged_in %}` nav block (currently only "Sign out" appears there), using `url_for('profile')`

## Files to change
- `app.py` — replace the `/profile` stub: require `session["user_id"]` (redirect to `login` if missing), fetch the user via a new `database/db.py` helper, render `profile.html`
- `database/db.py` — add `get_user_by_id(user_id)` following the same pattern as `get_user_by_email()` (parameterized query, `SELECT id, name, email, created_at`, returns `None` if not found)
- `templates/base.html` — add the profile nav link for logged-in users

## Files to create
- `templates/profile.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — no string formatting in SQL
- Passwords hashed with werkzeug (unchanged by this step; `get_user_by_id` must never select `password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `/profile` must redirect unauthenticated visitors to `/login` — never render account data without a valid session
- If `session["user_id"]` refers to a user that no longer exists (edge case), clear the session and redirect to `/login` rather than raising a 500
- Any currency or monetary figures shown must use ₹ (INR), consistent with the rest of the app — not applicable to this step since the profile page shows no monetary data, but keep in mind for later steps that build on this page
- Do not add editing, password-change, or expense-related functionality — this step is view-only

## Definition of done
- [ ] Visiting `/profile` while logged out redirects to `/login`, no profile data is exposed
- [ ] Visiting `/profile` while logged in renders `profile.html` with the correct name, email, and member-since date for the logged-in user (verify against the `users` table)
- [ ] The rendered page never displays `password_hash` or any password-related field
- [ ] The nav bar shows a "Profile" link when logged in, using `url_for('profile')` (no hardcoded `/profile` href)
- [ ] Clicking the nav "Profile" link from any page navigates to `/profile` successfully
- [ ] `profile.html` extends `base.html` and uses only CSS variables already defined in `style.css` (no hardcoded hex values)
- [ ] No new pip packages were added to `requirements.txt`
- [ ] App still starts cleanly on port 5001 with no errors
