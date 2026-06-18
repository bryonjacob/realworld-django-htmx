# Behavioral specs (FFFlow L3)

These Gherkin feature files are the **behavioral contract** for the app — what
it does, in present tense, in domain language. They were extracted from the
existing code by FFFlow's `characterize` step, so they describe current
behavior (characterization), not aspirations.

## Layout

One directory per bounded context (matching the Django apps + shared helpers):

```
docs/specs/
  accounts/    authentication, profiles & following, user model
  articles/    feeds, authoring, article model, markdown
  comments/    commenting, comment model
  helpers/     pagination, integrity-error classification, htmx detection
```

Acceptance specs live at a context root; domain/property specs live under
`<context>/domain/`. `*-properties.feature` files hold universal invariants
(tagged `@property-based`) suited to property-based testing with Hypothesis.

## RIDs (requirement IDs)

Every scenario carries a unique `@RID-{CONTEXT}-{NAME}-{NNN}` tag. The CONTEXT
segment matches the first directory under `docs/specs/`. These are the anchor
points for traceability: spec → test → code.

131 scenarios, 131 RIDs.

## Gates (both blocking, part of `just check-all`)

- **`just spec-audit`** — `specdrive audit`: every RID is well-formed, unique,
  and its CONTEXT matches its directory.
- **`just spec-verify`** — full spec→test traceability. Runs both test suites,
  emits a JUnit report from each, injects each test's RID(s), merges the
  reports, and runs `specdrive verify` with `strictTraceability` on.
  **131/131 RIDs covered, 0 uncovered.**

## How a test declares the scenario it covers

`specdrive verify` reads RIDs from the JUnit report as
`<property name="rid" value="RID-...">` inside each `<testcase>`. The Django
runner doesn't emit per-test properties, so the mapping lives in
`docs/specs/rid_map.*.yaml` (`"<classname>::<test_method>": [RID-...]`) and
`scripts/inject_rids.py` writes the properties into the report. 15 tests are
deliberately unmapped (`@NOSPEC`) — seed/CLI commands and bare GET-render
smoke tests with no behavioral scenario.

## Two test suites

- **Django suite** (`apps/*/tests.py`, `helpers/tests.py`, `manage.py test`) —
  the 124 example/behavioral tests, including `hypothesis.extra.django`
  property tests for DB-backed invariants (slug stability, email-identity,
  self-follow).
- **Property suite** (`specs/property/`, pytest + `pytest-bdd-property`) — binds
  the DB-free `@property-based` pagination scenarios directly to the Gherkin
  feature file; Hypothesis generates 100+ inputs per scenario.

## `@unverified-intent`

Seven scenarios carry a `# @unverified-intent:` comment. These pin behavior
that is *currently* true but may be an unintended quirk (e.g. a self-follow is a
silent no-op; an out-of-range page number echoes back rather than clamping).
They are documented as the contract and flagged for stakeholder review — not
silently "fixed."
