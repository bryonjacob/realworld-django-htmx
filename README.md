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

1. Clone with submodules and install dependencies

This project uses a Git submodule for static assets (CSS, icons, etc.) and the E2E test suite. You **must** initialize submodules when cloning:

```shell
git clone --recurse-submodules <repo-url>
cd realworld-django-htmx
make sync
```

If you already cloned without `--recurse-submodules`, initialize them manually:

```shell
git submodule update --init --recursive
```

2. Apply migrations and run

```shell
# SQLite (development)
DEBUG=True make migrate
make run-debug

# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@host:port/dbname make migrate
DATABASE_URL=postgresql://user:password@host:port/dbname ALLOWED_HOSTS=* make run
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

## License

- Original code by [Sean-Miningah](https://github.com/Sean-Miningah/) under [MIT License](https://github.com/Sean-Miningah/realWorld-DjangoRestFramework/blob/master/LICENSE)
- Django Ninja port by [c4ffein](https://github.com/c4ffein/) under [MIT License](https://github.com/c4ffein/realworld-django-ninja/blob/master/LICENSE)
- HTMX port also under [MIT License](LICENSE)
