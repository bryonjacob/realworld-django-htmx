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

# Check for security vulnerabilities (CRITICAL, fixable only)
vulns:
    grype dir:.venv --fail-on critical --only-fixed

# Analyze licenses (production deps only, fail on GPL/LGPL/AGPL)
lic:
    #!/usr/bin/env bash
    set -e
    [ ! -d .venv-lic ] && uv venv .venv-lic --quiet
    source .venv-lic/bin/activate
    uv pip install -e . --quiet
    uv pip install pip-licenses --quiet
    pip-licenses --fail-on="GPL;LGPL;AGPL" --partial-match --format=plain
    deactivate

# Generate software bill of materials (CycloneDX format)
sbom:
    syft dir:. --source-name realworld-django-htmx --source-version 0.1.0 -o cyclonedx-json > sbom.json
    @echo "📦 SBOM written to sbom.json"

# Check development environment health
doctor:
    #!/usr/bin/env bash
    echo "Required tools:"
    command -v just     >/dev/null && echo "✅ just     $(just --version)"     || echo "❌ just"
    command -v python3  >/dev/null && echo "✅ python3  $(python3 --version)"  || echo "❌ python3"
    command -v uv       >/dev/null && echo "✅ uv       $(uv --version)"       || echo "❌ uv"
    command -v node     >/dev/null && echo "✅ node     $(node --version)"     || echo "❌ node"
    command -v npm      >/dev/null && echo "✅ npm      $(npm --version)"      || echo "❌ npm"
    echo ""
    echo "Optional tools:"
    command -v grype    >/dev/null && echo "✅ grype    $(grype version | awk '/^Version:/ {print $2; exit}')" || echo "⚠️  grype (security scanning)"
    command -v syft     >/dev/null && echo "✅ syft     $(syft version | awk '/^Version:/ {print $2; exit}')"  || echo "⚠️  syft (SBOM generation)"
    command -v cloc     >/dev/null && echo "✅ cloc"     || echo "⚠️  cloc (used by 'just loc')"

# Remove generated files and artifacts
clean:
    find . -type d -name __pycache__ -exec rm -rf {} +
    rm -rf .pytest_cache .coverage htmlcov .ruff_cache .venv-lic
    rm -f sbom.json grype-report.json
