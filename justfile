set shell := ["bash", "-uc"]

# Show all available commands
default:
    @just --list

# Install dependencies and setup development environment
dev-install:
    make sync
    npm install --silent  # node tooling: specdrive (L3 spec audit), Playwright

# Format code (auto-fix)
format:
    uv run ruff format .

# Lint code (auto-fix, complexity threshold=10)
lint:
    make lint

# Type check code
typecheck:
    make type-check

# Run unit tests
test:
    make test-django-fast

# Run unit tests with coverage threshold (96%)
coverage:
    DEBUG=True DATABASE_URL="file:memdb1?mode=memory&cache=shared" USE_FAST_HASHER=True uv run --with coverage coverage run -m manage test apps helpers
    uv run --with coverage coverage report --fail-under=96
    uv run --with coverage coverage html
    @echo "📊 HTML report: htmlcov/index.html"

# Run integration tests with coverage report (no threshold)
integration-test:
    npm install --silent
    npx playwright install --with-deps chromium
    cd playwright && npx playwright test

# Detailed complexity report for refactoring decisions
complexity:
    uv run --with radon radon cc apps helpers config -a -s --no-assert

# Show N largest files by lines of code
loc N="20":
    cloc apps helpers config --by-file --quiet | head -n $(({{N}} + 5))

# Install FFFlow git hooks (pre-commit framework, delegates to justfile recipes)
hooks-install:
    @if command -v pre-commit >/dev/null; then \
        pre-commit install --hook-type pre-commit --hook-type pre-push; \
    else \
        echo "pre-commit not found — install it (uv tool install pre-commit) then re-run."; \
        exit 1; \
    fi

# Validate spec RIDs: format, uniqueness, context-match (FFFlow L3, blocking)
spec-audit:
    npx specdrive audit

# Show declared specs and RID counts
spec-status:
    npx specdrive status

# Run tests emitting JUnit XML, then cross-reference RIDs against the report.
# Non-blocking on this branch: tests are not yet RID-annotated, so verify
# reports untraced tests as informational. Turn on strictTraceability in
# specdrive.yaml once scenarios are wired to tests to make this a hard gate.
spec-verify:
    rm -rf test-reports
    DEBUG=True DATABASE_URL="file:memdb1?mode=memory&cache=shared" USE_FAST_HASHER=True \
        TEST_OUTPUT_DIR=test-reports \
        uv run python manage.py test apps helpers
    npx specdrive verify test-reports/junit.xml || echo "⚠ specdrive verify reported untraced tests (non-blocking on this branch)"

# Run all quality checks (format, lint, typecheck, coverage, spec-audit - fastest first)
check-all: format lint typecheck coverage spec-audit
    @echo "✅ All checks passed"

# Remove generated files and artifacts
clean:
    find . -type d -name __pycache__ -exec rm -rf {} +
    rm -rf .pytest_cache .coverage htmlcov .ruff_cache test-reports
