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

# Cross-reference every spec RID against a test that exercises it (blocking).
# Runs both suites — the Django suite (manage.py test) and the pytest-bdd
# property suite — emits a JUnit report from each, injects each test's RID(s)
# from docs/specs/rid_map.*.yaml, merges the reports, and runs specdrive verify.
spec-verify:
    rm -rf test-reports
    mkdir -p test-reports
    # 0. Merge the per-context rid maps (single source of truth) into one.
    uv run --with pyyaml python scripts/merge_rid_maps.py test-reports/rid_map.django.yaml docs/specs/rid_map.accounts.yaml docs/specs/rid_map.articles.yaml docs/specs/rid_map.comments.yaml docs/specs/rid_map.helpers.yaml
    # 1. Django suite -> JUnit, inject RIDs from the merged map
    DEBUG=True DATABASE_URL="file:memdb1?mode=memory&cache=shared" USE_FAST_HASHER=True \
        TEST_OUTPUT_DIR=test-reports \
        uv run python manage.py test apps helpers
    uv run --with pyyaml python scripts/inject_rids.py test-reports/junit.xml test-reports/rid_map.django.yaml
    # 2. pytest property suite -> JUnit, inject property RIDs
    DEBUG=True DATABASE_URL="file:memdb1?mode=memory&cache=shared" USE_FAST_HASHER=True \
        uv run pytest specs/property/ --junitxml=test-reports/property.xml -q
    uv run --with pyyaml python scripts/inject_rids.py test-reports/property.xml docs/specs/rid_map.property.yaml
    # 3. merge both reports and verify full traceability
    uv run python scripts/merge_junit.py test-reports/merged.xml test-reports/junit.xml test-reports/property.xml
    npx specdrive verify test-reports/merged.xml

# Run all quality checks (format, lint, typecheck, coverage, spec-audit, spec-verify)
check-all: format lint typecheck coverage spec-audit spec-verify
    @echo "✅ All checks passed"

# Remove generated files and artifacts
clean:
    find . -type d -name __pycache__ -exec rm -rf {} +
    rm -rf .pytest_cache .hypothesis .coverage htmlcov .ruff_cache test-reports
