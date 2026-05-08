# Roadmap

Hypothetical product roadmap for **realworld-django-htmx** — features the RealWorld spec leaves out but a real Medium-class blogging app would have. Each entry links to a one-page PRD intended as directional input for a planning session, not an implementable spec.

PRD format: see [`PRD_TEMPLATE.md`](PRD_TEMPLATE.md). Files are numbered `NN.MM Title.md` so they sort lexically by tier.

## Tier 1 — Table-stakes

The RealWorld spec is intentionally minimal. These are the gaps any real signup-and-publish product fills before launch.

- [10.01 Password Reset and Email Verification](prds/10.01%20Password%20Reset%20and%20Email%20Verification.md) — signup is bare today; add Django's built-in flows + transactional email.
- [10.02 Article Search](prds/10.02%20Article%20Search.md) — tags filter exists but no title/body search; Postgres full-text in prod, LIKE fallback in dev.
- [10.03 Article Drafts and Unpublish](prds/10.03%20Article%20Drafts%20and%20Unpublish.md) — articles publish immediately; add a `status` field and a "My Drafts" tab.
- [10.04 Image Uploads](prds/10.04%20Image%20Uploads.md) — `User.image` is a URLField; add cover-image and avatar uploads via S3-compatible storage.
- [10.05 Markdown Rendering](prds/10.05%20Markdown%20Rendering.md) — bodies and comments render plain text today; add Markdown + sanitization + preview.
- [10.06 Account Deletion and Data Export](prds/10.06%20Account%20Deletion%20and%20Data%20Export.md) — GDPR table-stakes: self-serve delete and JSON export.

## Tier 2 — Engagement

Things that turn a blog clone into something users come back to.

- [20.01 Notifications](prds/20.01%20Notifications.md) — bell icon with HTMX polling; "favorited / commented / followed" events.
- [20.02 Comment Threading](prds/20.02%20Comment%20Threading.md) — replace flat comments with a depth-capped reply tree.
- [20.03 Article Reactions](prds/20.03%20Article%20Reactions.md) — Medium-style claps (1–50 per user) alongside the binary favorite.
- [20.04 Reading List](prds/20.04%20Reading%20List.md) — private bookmarks distinct from public favorites.
- [20.05 Rich Profiles](prds/20.05%20Rich%20Profiles.md) — pinned article, social links, follower counts, member-since.
- [20.06 Tag Pages and Tag Following](prds/20.06%20Tag%20Pages%20and%20Tag%20Following.md) — landing page per tag, follow-a-tag, tag-feed branch.

## Tier 3 — Platform

Polish, trust, and reach. The product feels grown-up after these.

- [30.01 Editor Improvements](prds/30.01%20Editor%20Improvements.md) — autosave, inline image upload, live Markdown preview.
- [30.02 Reading Time and View Counts](prds/30.02%20Reading%20Time%20and%20View%20Counts.md) — words/265 wpm read-time; deduped view counter.
- [30.03 RSS and Atom Feeds](prds/30.03%20RSS%20and%20Atom%20Feeds.md) — Django syndication: global, per-author, per-tag.
- [30.04 Moderation](prds/30.04%20Moderation.md) — report button, soft-delete, admin queue, rate limits.
- [30.05 Two-Factor Auth](prds/30.05%20Two-Factor%20Auth.md) — TOTP via django-otp; forced for staff.
- [30.06 Public Read-Only API](prds/30.06%20Public%20Read-Only%20API.md) — django-ninja endpoints; revisits the "no API" thesis with explicit narrow scope.

## Tier 4 — Operational

What the project needs to actually run in production. SRE/platform, less product-y.

- [40.01 Observability](prds/40.01%20Observability.md) — structured logs, request IDs, Sentry, health endpoints.
- [40.02 Background Jobs](prds/40.02%20Background%20Jobs.md) — django-q2 + Redis for email, fan-out, indexing, thumbnails.
- [40.03 Caching](prds/40.03%20Caching.md) — per-view cache for the global feed, fragment cache for article cards.
- [40.04 Deployment Story](prds/40.04%20Deployment%20Story.md) — Dockerfile, Postgres migration, Fly.io as the primary target.

## Cross-cutting dependencies

Stitched together from the four agent teams' reports — these are the threads that cut across tiers:

- **40.01 Observability + 40.04 Deployment land first.** They're not blocked by anything and they unblock everything else operationally. Run them in parallel.
- **40.02 Background Jobs unblocks the async path** for 10.01 (email send), 20.01 (notification fan-out), 10.02 (search indexing), and 10.04 (thumbnail generation). Build it once; reuse it everywhere.
- **10.05 Markdown Rendering is load-bearing** for 10.03 (draft preview), 30.01 (live editor preview), 30.03 (feed bodies), and 30.06 (API `bodyHtml`). Land it early in Tier 1.
- **10.01 Email Verification is a soft prereq** for 10.06 (deletion receipt), 30.04 (per-user rate limits), and 30.05 (don't enable 2FA on top of unverified email).
- **20.01 Notifications is the connective tissue of Tier 2.** 20.02, 20.03, and 20.06 all generate events worth notifying on. Land 20.01 first if shipping more than one of them.
- **20.03 Reactions + 20.04 Reading List compete for article-card real estate.** Whichever ships second should mock the card with all three icons (favorite, clap, bookmark) before merging.
- **`_feed_queryset` is the shared extension point** for 10.02 Search, 10.03 Drafts, 20.04 Reading List, and 20.06 Tag Following. If two land in the same cycle, refactor it once to a dispatch table rather than stacking branches.

## Suggested first slice

If we had to pick **three** PRDs that give the most product value per line of code while keeping the "no SPA, no API" thesis intact: **10.01 Password Reset**, **10.03 Drafts**, **20.01 Notifications**. All three are natural HTMX partial flows; together they take the project from "spec demo" to "actually usable."

Operational prereqs for that slice: **40.01 Observability** and **40.04 Deployment** first, then **40.02 Background Jobs** to take email + fan-out off the request path.
