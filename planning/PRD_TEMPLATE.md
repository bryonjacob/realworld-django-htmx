# PRD: <Feature Name>

**Tier:** <1 | 2 | 3 | 4> &nbsp;·&nbsp; **Status:** Proposed &nbsp;·&nbsp; **Owner:** TBD

## Problem
<2–4 sentences. Who feels the pain today, what they can't do, and why it matters for a RealWorld-class blogging app. Reference the gap vs. the current implementation, not vs. the RealWorld spec.>

## Goals
- <Outcome 1 — observable user-facing or operational change>
- <Outcome 2>
- <Outcome 3 — keep to 3–5; sharper is better>

## Non-Goals
- <Explicitly out of scope. Naming these now prevents scope creep in planning.>
- <…>

## User Stories
- As a <role>, I can <action> so that <outcome>.
- As a <role>, I can <action> so that <outcome>.
- <3–6 stories covering the golden path + 1–2 important edges>

## UX Sketch
<Plain-prose description of the surfaces touched. Where does this live in the nav? What partials or new templates are involved? HTMX interactions (swap targets, triggers) called out at a high level. No mockups required — words are fine.>

## Data Model Changes
<New models, new fields, new indexes, M2M tables. One bullet per change. Note nullability and migration shape (additive vs. destructive). If none, write "None.">

## Key Technical Decisions
- <Decision + rationale. E.g. "Use Django's built-in PasswordResetView rather than rolling our own — battle-tested, fits stack.">
- <Library choices, with the alternative considered.>
- <Anything that affects the "no API, no SPA" thesis or the 100% coverage gate.>

## Risks & Open Questions
- <Risk: what could go wrong, and the mitigation or the question to resolve in planning.>
- <Open question the team needs to answer before breaking this into issues.>

## Success Metrics
- <How we'll know it landed. E.g. "% of signups that verify email within 24h", "p95 search latency < 200ms", "0 regressions in e2e baseline".>

## Rough Effort
<S | M | L | XL>  — <one sentence justifying the size: surfaces touched, migration risk, new dependencies>

## Dependencies
- <Other PRDs or infra that must land first, or "None">
