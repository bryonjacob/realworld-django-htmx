# apps/accounts

User model, auth views, profile routing.

## Purpose

Owns the custom `User` model, the login/register/settings/logout flows, and the URL routing for `/profile/<username>` (the actual profile rendering logic lives in `apps/articles/views.py::profile_view` — this app just keeps the URLs and the delegating shims).

## Key components

- **models.py** — `User(AbstractUser)` with email as the `USERNAME_FIELD`, plus a self-referential M2M `followers`. Has `is_following(other_user)` for template checks. `UserManager` overrides `create_user` / `create_superuser`.
- **views.py** — `login_view`, `register_view`, `settings_view`, `logout_view`, `follow_view`, plus two thin `profile_view` / `profile_favorites_view` shims that delegate to `articles.views.profile_view`.
- **forms.py** — `LoginForm`, `RegisterForm`, `SettingsForm` (a `ModelForm`). Field names must match the RealWorld SELECTORS.md contract — **don't rename them**.
- **urls.py** — `/login`, `/register`, `/settings`, `/logout`, `/profile/<username>`, `/profile/<username>/favorites`, `/profile/<username>/follow`.

## Non-obvious things

- `User.USERNAME_FIELD = "email"` — auth uses email, not the username field, for login. `username` is a display/URL handle only.
- `create_user` sets an unusable password if none given. Used by `seed_data` management command.
- `follow_view` is HTMX-aware: returns a partial if `HX-Request` header is set, otherwise redirects. Same pattern throughout the project.
- The `accounts/profile_404.html` template is used when a profile URL hits a missing user — intentional custom 404, not Django's default.
- Do **not** re-introduce `from articles.models import Article` here. That was the layering violation we fixed in the `refactor-pass` epic (see repo root CLAUDE.md).

## Dependencies

- **Uses**: `articles.views.profile_view` (thin shim only; no model imports), `helpers.exceptions`, `helpers.htmx`.
- **Used by**: nothing (accounts is a leaf — other apps import `User` via `get_user_model()` / `settings.AUTH_USER_MODEL`, not directly).
