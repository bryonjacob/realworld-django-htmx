# helpers/

Cross-app utilities. Zero reverse dependencies — helpers depends on nothing else in the project, everything else depends on it.

## Modules

- **pagination.py** — `paginate(queryset, request, per_page)` + `Page` dataclass. Parses `?page=` from query string, slices the queryset, returns items + page number + page range for template rendering. Invalid input (non-int, zero, negative) defaults to page 1 — **do not use Django's built-in `Paginator`**, which raises on invalid input and breaks e2e pagination tests. Introduced in the `refactor-pass` epic to kill duplication between `articles/views._build_feed` and the profile view.
- **htmx.py** — `is_htmx(request) -> bool`. Checks the `HX-Request` header. Used in every view that returns a partial template for HTMX requests and a full template otherwise.
- **exceptions.py** — `ResourceNotFound`, `get_or_404`, and `clean_integrity_error`. The last one parses database driver error messages (SQLite and psycopg2) to extract which unique constraint was violated, for converting `IntegrityError` into a nice form error. Tests cover both drivers.
- **context_processors.py** — `conduit_context(request)` provides `conduit_user_json` and `conduit_authenticated` to every template. Registered in `config/settings.py::TEMPLATES`.
- **tests.py** — unit tests for the above. Uses `unittest.TestCase` for pure functions (no DB), `django.test.TestCase` for database-backed ones.

## Patterns to preserve

- **No reverse dependencies.** `helpers/` must not import from `apps/`. If something in helpers needs an app-level type, parameterize it or move it to the relevant app. This keeps the module usable from anywhere without cycles.
- **`paginate()` is queryset-generic.** When adding a new paginated page, import `paginate` and pass your queryset — don't write offset math inline.
- **No `# type: ignore`.** Type issues get fixed at the source. The `clean_integrity_error` function, for example, binds `cause = error.__cause__` to a local so `ty` can narrow through `isinstance` checks (see commit `16fd1d3`).
- **`is_htmx` check at the bottom of the view**, not at the top — build the full context first, then pick which template to render. This keeps the full-page and HTMX-partial code paths identical.
