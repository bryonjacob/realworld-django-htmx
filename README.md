# AAIA Summer Intensive 2026 Workshop — Medium App Clone

This repository is the shared starting point for the AAIA Summer Intensive 2026
development workshop. It is a working **Medium clone ("Conduit")** built with
**Django + HTMX** — a real application with real complexity: authentication,
articles, comments, tags, favorites, following, and feeds.

It is cloned from the upstream open-source project
[c4ffein/realworld-django-htmx](https://github.com/c4ffein/realworld-django-htmx)
and prepared so that everyone in the workshop builds from the **same
application**. The upstream project pulls its CSS, icons, and end-to-end test
suite from a Git submodule; we have **inlined all of that directly into the
repository** — so there is no submodule step. You clone, install, and run.

## Getting started

The only prerequisite is [uv](https://docs.astral.sh/uv/) (which manages Python
and all dependencies for you).

```shell
# 1. Clone the repository
git clone <your-assigned-repo-url>
cd <repo-directory>

# 2. Install dependencies (Python + packages)
uv sync --extra dev

# 3. Set up the database
DEBUG=True uv run python manage.py migrate

# 4. Start the app
DEBUG=True uv run python manage.py runserver 0.0.0.0:8000
```

Then open **http://localhost:8000** — you should see the Conduit home page,
fully styled. Register an account from the **Sign up** link and start using the
app.

---

# ![RealWorld Example App](logo.png)

> ### Django + HTMX codebase containing real world examples (CRUD, auth, advanced patterns, etc) that adheres to the [RealWorld](https://github.com/realworld-apps/realworld) spec.

### [RealWorld](https://github.com/realworld-apps/realworld)

A fullstack [RealWorld](https://github.com/realworld-apps/realworld) implementation (Medium clone) using **Django** for server-rendered HTML and **HTMX** for interactive elements — no API, no SPA.

#### Architecture

- **Views** use Django session auth, standard forms, and `@login_required`
- **HTMX** handles interactive elements: favorites, follows, comments, feed pagination/tab switching
- **E2E tests** validate the fullstack behavior via Playwright

#### Origin

Ported from [c4ffein/realworld-django-ninja](https://github.com/c4ffein/realworld-django-ninja), itself based on [Sean-Miningah/realWorld-DjangoRestFramework](https://github.com/Sean-Miningah/realWorld-DjangoRestFramework).

For more RealWorld implementations, see [codebase.show](https://codebase.show/projects/realworld).

## Usage

For local development, see [**Getting started**](#getting-started) above. Static
assets (CSS, icons) and the E2E test suite are inlined directly into this
repository — there is no submodule to initialize.

The project also ships `make` targets that wrap the same commands (`make sync`,
`DEBUG=True make migrate`, `make run-debug`).

For PostgreSQL instead of the default development SQLite:

```shell
DATABASE_URL=postgresql://user:password@host:port/dbname uv run python manage.py migrate
DATABASE_URL=postgresql://user:password@host:port/dbname ALLOWED_HOSTS=* uv run python manage.py runserver 0.0.0.0:8000
```

### Using Docker

```shell
docker compose up          # run
docker compose up --build  # rebuild and run
```

## Testing

This project uses `just` as its primary task runner (see `justfile`). Legacy `make` targets still work.

| Command | Description |
|---------|-------------|
| `just check-all` | Lint + type-check + unit tests (with 96% coverage gate, actual 100%) |
| `just test` | Unit tests only (fast, in-memory SQLite, fast hasher) |
| `just coverage` | Unit tests + HTML coverage report at `htmlcov/index.html` |
| `just integration-test` | Playwright e2e tests (uses `npx`, no bun dependency) |
| `make test-django-fast` | Unit tests via Make (legacy) |
| `make e2e` | Playwright via `bun` (legacy; prefer `just integration-test`) |
| `make verify` | Make equivalent of `just check-all` (legacy) |

### Current test status

- **Unit tests:** 107/107 passing, 100% coverage across all production code. Per-app test modules (`apps/*/tests.py`) plus `helpers/tests.py`, using `django.test.Client` against in-memory SQLite with the fast password hasher — full suite runs in ~0.5s.
- **E2E tests:** 74/74 passing, 65 API-only tests skipped via `API_MODE=false`. The [RealWorld e2e suite](https://github.com/realworld-apps/realworld) validates browser behavior end to end.

## Development

Primary tooling is `just`:

- `just format` — auto-fix formatting (ruff)
- `just lint` — check linting rules
- `just typecheck` — run ty type checker (zero diagnostics on current `main`)
- `just complexity` — per-function complexity report (radon)
- `just loc` — largest files by LOC (cloc)
- `just clean` — remove caches, coverage artifacts, `__pycache__`

Legacy `make lint` / `make lint-check` / `make type-check` / `make clean` still work and are delegated to by the corresponding `just` recipes where applicable.

### Per-module documentation

The codebase has a `CLAUDE.md` file in every meaningful module (`apps/`, each of the three apps, `config/`, `helpers/`, `templates/`, `playwright/`). Start there when navigating an unfamiliar area.

### FFFlow development workflow (optional)

This repository is set up to use [FFFlow](https://github.com/bryonjacob/ffflow-plugin),
a Claude Code plugin for spec-driven development (plan → work → audit). The
plugin's commands (`/fff:*`) are declared in `.claude/settings.json`, so when you
open this folder in Claude Code and trust it, you'll be prompted to install the
`fff` plugin automatically.

The plugin is **only needed to invoke the `/fff:*` workflow commands**. Running
the app and the quality gates (`just check-all`) does **not** require it — the
FFFlow artifacts it produced (Gherkin specs under `docs/specs/`, the `justfile`
gates, `specdrive.yaml`, the test suites) are plain files committed to the repo.

## License

- Original code by [Sean-Miningah](https://github.com/Sean-Miningah/) under [MIT License](https://github.com/Sean-Miningah/realWorld-DjangoRestFramework/blob/master/LICENSE)
- Django Ninja port by [c4ffein](https://github.com/c4ffein/) under [MIT License](https://github.com/c4ffein/realworld-django-ninja/blob/master/LICENSE)
- HTMX port also under [MIT License](LICENSE)
