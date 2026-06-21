########################
# Variables

MEMDB := "file:memdb1?mode=memory&cache=shared"

########################
# Django Project

help:
	@echo "Available commands:"
	@echo "  sync"
	@echo "  run-debug"
	@echo "  run"
	@echo "  migrate"
	@echo "  test-django"
	@echo "  test-django-fast"
	@echo "  lint"
	@echo "  lint-check"
	@echo "  type-check"
	@echo "  verify"
	@echo "  e2e             - run e2e tests (auto-starts in-memory SQLite server)"
	@echo "  clean           - remove all __pycache__ directories"

sync:
	uv sync --extra dev

run-debug:
	DEBUG=True uv run python manage.py runserver 0.0.0.0:8000

migrate:
	uv run python manage.py migrate

run:
	uv run python manage.py runserver 0.0.0.0:8000

test-django:
	DEBUG=True uv run python manage.py test apps helpers

test-django-fast:
	DEBUG=True DATABASE_URL=$(MEMDB) USE_FAST_HASHER=True uv run python manage.py test apps helpers

lint:
	uv run ruff check --fix; uv run ruff format

lint-check:
	uv run ruff check --no-fix && uv run ruff format --check

type-check:
	uv run ty check

verify:
	make lint-check && make type-check && make test-django-fast

e2e:
	cd playwright && API_MODE=false API_BASE=http://localhost:8000/api bun playwright test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
