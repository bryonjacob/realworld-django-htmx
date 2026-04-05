# playwright/

Playwright e2e test harness. Runs the shared RealWorld spec against this implementation.

## Files

- **playwright.config.ts** — the whole config. Points at `realworld/specs/e2e` (git submodule) for test files, auto-starts a Django dev server via the `webServer` block, runs in a single worker (no parallelism).

## How it runs

1. `just integration-test` runs `cd playwright && npx playwright test` (or `API_MODE=false npx playwright test` directly)
2. Playwright's `webServer` block starts Django with `DEBUG=True`, in-memory SQLite (`file:memdb1?mode=memory&cache=shared`), `USE_FAST_HASHER=True`. It runs migrations, then `seed_data`, then `runserver --noreload` on port 8000.
3. Tests hit `http://localhost:8000` via the browser. Each test manages its own user via the register flow.
4. When Playwright exits, the dev server is torn down.

## API_MODE and skipped tests

The RealWorld e2e suite is shared across implementations, including API-based ones. ~65 tests are API-only (they hit `/api/user`, `/api/articles`, etc., which this implementation does not have). They gate themselves with `test.skip(!API_MODE, ...)` at the top of each test, so passing `API_MODE=false` (the default here) causes them to self-skip rather than fail.

**Expected baseline**: 74 passed, 65 skipped, 0 failed. Deviations from this are the test signal — if the passed count drops, a regression was introduced; if the failed count goes up, investigate first (the spec sometimes drifts with submodule updates).

## Why npx and not bun

The original `make e2e` target uses `bun` per upstream, but we don't ship bun in all environments. `just integration-test` uses `npx playwright test` instead — same tests, same config, no bun dependency. Both paths work.

## Test artifacts

- `test-results/` — failure screenshots, videos, traces. Regenerated every run; in `.gitignore`.
- `playwright-report/` — HTML report. Regenerated every run; in `.gitignore`.
- `node_modules/` — `@playwright/test` and its deps. In `.gitignore`.

## Never modify test files from here

The specs live in `realworld/specs/e2e/*.spec.ts` (git submodule). That's upstream content. If a test is wrong for this implementation, fix it upstream or filter it via `API_MODE` — don't edit the submodule directly.
