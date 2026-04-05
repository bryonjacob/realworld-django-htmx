# config/

Django project configuration: settings, URL conf, WSGI/ASGI entry points.

## Key components

- **settings.py** — the single settings module. Reads env vars at import time.
- **urls.py** — top-level URL conf. Includes each app's `urls.py`; no API routes (no `/api/*`).
- **wsgi.py** / **asgi.py** — standard Django deployment entry points.

## Non-obvious things about settings.py

- **`apps/` is injected into `sys.path`** at line 16. This is what makes `from accounts.models import User` work across the codebase. If you move files around, this line is load-bearing.
- **Database selection is env-var driven with three modes:**
  1. `DATABASE_URL` starts with `:memory:` or `file:` → in-memory SQLite (used by unit tests and Playwright webServer)
  2. `DATABASE_URL` set otherwise → parsed as PostgreSQL
  3. `DEBUG=True` with no `DATABASE_URL` → file-based SQLite (`db.sqlite3` in repo root)
  4. Anything else → `raise SystemExit` with a helpful error
- **`USE_FAST_HASHER=True`** switches to `MD5PasswordHasher` for test speed. Only allowed with `DEBUG=True` (raises otherwise). This is why `just test-django-fast` runs in ~0.4s.
- **`AUTH_USER_MODEL = "accounts.User"`** — custom user model. Any new foreign key to users should use `settings.AUTH_USER_MODEL`, not `from accounts.models import User` directly (prevents circular import risks).
- **Environment branches have `# pragma: no cover`** on the Postgres, raise-on-misconfig, and file-SQLite-default lines. These aren't exercised by the test runner but are exercised in real deployment — not dead code, just untestable under our test env.

## Template context processors

`helpers.context_processors.conduit_context` is registered — it exposes `conduit_user_json` and `conduit_authenticated` to every template. Used by `templates/base.html` to set `window.__conduit_debug__` for browser-console debugging.
