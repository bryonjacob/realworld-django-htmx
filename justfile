set shell := ["bash", "-uc"]

# Show all available commands
default:
    @just --list

# Install dependencies and setup development environment
dev-install:
    make sync

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

# Run all quality checks (format, lint, typecheck, coverage - fastest first)
check-all: format lint typecheck coverage
    @echo "✅ All checks passed"

# Remove generated files and artifacts
clean:
    find . -type d -name __pycache__ -exec rm -rf {} +
    rm -rf .pytest_cache .coverage htmlcov .ruff_cache
