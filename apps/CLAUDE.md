# apps/

Three Django apps, one per domain. Kept deliberately thin and layered.

## Apps

- **accounts** — users, auth, profile pages. Custom `User` model extending `AbstractUser`, email-as-username.
- **articles** — articles, feeds, tags, favorites. Owns `profile_view` since profiles are mostly article lists.
- **comments** — article comments. Depends on articles; nothing depends on comments.

## Layering

Import direction is **one-way**: `accounts → articles`, `comments → articles`. Nothing imports from `accounts` into the others. `articles` is the center; `comments` and `accounts` wrap it.

This is deliberate. The layering violation where `accounts/views.py` imported `Article` was fixed in the `refactor-pass` epic by moving the profile-view body into `articles/views.py` while keeping the URL routed through `accounts/urls.py`.

## sys.path note

`config/settings.py` adds `apps/` to `sys.path`, so imports inside these apps look like `from articles.models import Article` — **not** `from apps.articles.models import Article`. This is load-bearing for tests, URL routing, and the Django app registry. If you see a tool (mypy, pyright, editor) complain about unresolved imports, that's why; `ty` is configured to ignore `unresolved-import` in `pyproject.toml`.
