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

## Gates

- **`just spec-audit`** (blocking, part of `just check-all`) — runs
  `specdrive audit`: verifies every RID is well-formed, unique, and its CONTEXT
  matches its directory. Currently green.
- **`just spec-verify`** (non-blocking) — runs the test suite emitting a JUnit
  XML report, then `specdrive verify` cross-references test RIDs against the
  spec RIDs. Currently reports all 131 RIDs as *uncovered* because the existing
  tests are not yet annotated with the RID of the scenario they exercise.

## The workshop exercise

Wiring those 107 tests to the 131 scenario RIDs — so `specdrive verify` shows
coverage and `strictTraceability` can be turned on in `specdrive.yaml` — is the
hands-on exercise. A test declares the scenario it covers by emitting the RID
as a JUnit `<property name="rid" value="RID-...">`, or as a fallback by
including the `@RID-...` tag in the test name.

## `@unverified-intent`

Seven scenarios carry a `# @unverified-intent:` comment. These pin behavior
that is *currently* true but may be an unintended quirk (e.g. a self-follow is a
silent no-op; an out-of-range page number echoes back rather than clamping).
They are documented as the contract and flagged for stakeholder review — not
silently "fixed."
