"""
Shared pytest fixtures for the Spendly test suite.

Key constraint (see CLAUDE.md / task brief): `database/db.py` resolves
`DB_PATH` relative to its own file location to a real on-disk SQLite file
(`expense_tracker.db`), and `app.py` runs `init_db()` + `seed_db()` at
MODULE IMPORT TIME inside `with app.app_context(): ...`. That means simply
`import app` is enough to touch whatever `database.db.DB_PATH` currently
points at.

To keep tests fully isolated from the real dev database, we must:
  1. Create a temp file path for this test session/test.
  2. monkeypatch `database.db.DB_PATH` to that temp path.
  3. Reload `database.db` and `database.queries` (queries.py does
     `from database.db import get_db`, so it must be reloaded too, after
     db.py, so its reference points at the freshly-patched module) and
     THEN import/reload `app` so its own module-level
     `init_db(); seed_db()` call runs against the temp DB.

Each test gets a brand-new temp DB file (fresh seed data: one demo user
demo@spendly.com / demo123, plus 8 seed expenses across 7 categories).
"""
import sys

import pytest


@pytest.fixture
def app(monkeypatch, tmp_path):
    """A Spendly Flask app instance wired to an isolated, freshly-seeded temp DB.

    Named `app` per pytest-flask convention so `client` (provided by
    pytest-flask) resolves automatically.
    """
    # 1. Unique temp DB file per test — never touches the real dev DB.
    temp_db_path = tmp_path / "test_expense_tracker.db"

    # 2. Purge any previously-imported copies of the modules under test so
    #    reimporting actually re-executes their module-level code (including
    #    app.py's import-time init_db()/seed_db() call) against the patched path.
    for mod_name in ("app", "database.queries", "database.db"):
        sys.modules.pop(mod_name, None)

    # 3. Import database.db first and patch DB_PATH on it before anything
    #    else can call get_db() against the old path.
    import database.db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", str(temp_db_path))

    # 4. Reload database.queries so its `from database.db import get_db`
    #    binding refers to the already-patched db module (it was popped
    #    above, so this import re-executes it fresh).
    import database.queries  # noqa: F401

    # 5. Now import app — its module-level `init_db(); seed_db()` runs here,
    #    against the patched temp DB path, seeding the demo user + expenses.
    import app as app_module

    flask_app = app_module.app
    flask_app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "WTF_CSRF_ENABLED": False,
        }
    )

    yield flask_app

    # Cleanup: drop the module cache entries again so the next test's
    # fixture invocation gets a truly fresh reimport rather than reusing
    # this test's already-initialized modules/connections.
    for mod_name in ("app", "database.queries", "database.db"):
        sys.modules.pop(mod_name, None)


@pytest.fixture
def logged_in_client(client):
    """A Flask test client already authenticated as the seeded demo user.

    seed_db() creates exactly one user: demo@spendly.com / demo123.
    """
    response = client.post(
        "/login",
        data={"email": "demo@spendly.com", "password": "demo123"},
        follow_redirects=True,
    )
    assert response.status_code == 200, "Expected demo user login to succeed"
    return client
