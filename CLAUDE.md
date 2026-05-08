# realworld-django-htmx
**Django + HTMX fullstack implementation of the RealWorld spec — no API, no SPA**

## Rules

- **NEVER raise timeouts** without asking first. We build fast software. If a test times out, the code is broken — fix the code, don't raise the timeout. Raising timeouts destroys the feedback loop.
- **NEVER use `# type: ignore`**. Fix type issues at the source. If `ty` complains, the fix is in the code (narrow with an `isinstance`, bind a local, use a concrete type) — not in a suppression comment.
- **NEVER rename form field names** (`email`, `password`, `title`, `description`, `body`, etc.) or visible text labels (`Sign in`, `Your Feed`, `Publish Article`, etc.) without checking `realworld/specs/e2e/SELECTORS.md`. The e2e suite pins these.

## Before finishing

Run `just check-all` (lint + type-check + unit tests + 100% coverage gate). Optionally run `just integration-test` for the full Playwright e2e suite (baseline: 74 passed, 65 skipped, 0 failed).

## Testing

When asked to "run the tests", run both `just check-all` and `just integration-test`. Unit tests live per-app (`apps/*/tests.py`) plus `helpers/tests.py`, covering views, models, forms, and helpers via `django.test.Client`. E2e tests are the shared RealWorld spec (git submodule at `realworld/specs/e2e/`) driven by Playwright.

- **Unit tests**: fast, ~0.5s, in-memory SQLite + MD5 hasher, 100% coverage.
- **E2e tests**: slower, ~2.5min, real browser against a spawned Django dev server.

Both need to pass before a change is done.

## Commands

Primary tooling is `just` (see `justfile`). Legacy `make` targets still work and are delegated to by some `just` recipes.

- `just dev-install` — install deps (`uv sync --extra dev`)
- `just check-all` — format, lint, typecheck, coverage (enforced 96% floor, actual 100%)
- `just test` — unit tests only (fast)
- `just coverage` — unit tests + coverage report (HTML at `htmlcov/index.html`)
- `just lint` / `just format` / `just typecheck` — individual gates
- `just integration-test` — Playwright e2e suite (auto-starts Django webServer)
- `just complexity` — radon complexity report
- `just loc` — largest files by LOC
- `just clean` — remove caches and coverage artifacts

Running the server:

- `DEBUG=True make run-debug` — dev server on http://localhost:8000
- `DEBUG=True make migrate` — apply migrations

## Per-module docs

There's a `CLAUDE.md` in every meaningful module:

- `apps/CLAUDE.md` — app layering rules, `sys.path` note
- `apps/accounts/CLAUDE.md`, `apps/articles/CLAUDE.md`, `apps/comments/CLAUDE.md` — per-app purpose, components, gotchas
- `config/CLAUDE.md` — Django settings, env-var database selection, `# pragma` branches
- `helpers/CLAUDE.md` — shared utilities (`paginate`, `is_htmx`, `clean_integrity_error`)
- `templates/CLAUDE.md` — full-page vs partial split, selectors contract
- `playwright/CLAUDE.md` — e2e harness, API_MODE, baseline

## Roadmap

Hypothetical product roadmap (not committed work) lives in `planning/ROADMAP.md`, with one-page PRDs under `planning/prds/` covering features the RealWorld spec leaves out — drafts, search, notifications, deployment, etc. Use it as directional input for planning sessions, not as a spec.
