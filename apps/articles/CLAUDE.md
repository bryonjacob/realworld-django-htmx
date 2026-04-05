# apps/articles

Articles, feeds, tags, favorites, and the profile-page renderer.

## Purpose

The core content app. Owns everything about articles themselves (model, CRUD views, feed composition, tag handling, favorites) and — after the `refactor-pass` epic — also owns the profile-page view body because profiles are mostly article lists.

## Key components

- **models.py** — `Article` model plus an `ArticleQuerySet` with `with_favorites(user)` that annotates each row with `num_favorites` and `is_favorite`. Slug is auto-generated once on create via `Article.save()` and **stable on edit** (per commit `ae3c5ed`).
- **views.py** — the biggest view file in the project. Contains:
  - `home_view` / `tag_view` — both delegate to `_build_feed(request, tag=...)`
  - `_build_feed` — orchestrator: parses `?feed=`/`?page=`, calls `_feed_queryset`, redirects anonymous users away from the following feed, paginates, caches tags, picks template (full page vs HTMX partial)
  - `_feed_queryset(user, feed, tag) -> (QuerySet | None, str)` — private helper that returns the filtered article queryset + active-tab string. Returns `(None, "following")` when anonymous users request the following feed (caller redirects to login). Single extraction point for new feed types (drafts, bookmarks, search).
  - `article_detail_view`, `article_create_view`, `article_edit_view`, `article_delete_view`, `article_favorite_view`
  - `_save_article_form(form, article)` — private helper that translates form field names (`description`, `body`) to model field names (`summary`, `content`). **Don't rename either side** — form names are pinned by the RealWorld SELECTORS.md contract.
  - `profile_view(request, username, tab)` — the actual profile page renderer. Called by shims in `accounts/views.py`. Handles "my articles" and "favorites" tabs with per-tab querysets.
- **constants.py** — `ARTICLES_PER_PAGE`, `ALL_TAGS_CACHE_KEY`, `ALL_TAGS_CACHE_TTL_SECONDS`. Introduced in the `refactor-pass` epic to replace magic values.
- **forms.py** — `ArticleForm` with fields `title`, `description`, `body`, `tags`. Field names match the RealWorld SELECTORS.md contract.
- **admin.py** — auto-registers every model in the project via `apps.get_models()`. Lives here for historical reasons — code smell but harmless.
- **management/commands/seed_data.py** — creates `johndoe` / `janedoe` users and 8 articles. Used by Playwright's `webServer` block.
- **templatetags/markdown_filter.py** — `render_markdown` filter that sanitizes via `nh3.clean()`. Used in article detail pages.

## Non-obvious things

- Feed selection logic lives in `_feed_queryset`. If you're adding a new feed type (drafts, search, bookmarks), that's the one function to extend — everything downstream (pagination, HTMX partials, template) flows from its return value.
- The tag list is cached for 5 minutes under `ALL_TAGS_CACHE_KEY`. `_save_article_form` invalidates the cache on article save so new tags show up immediately on the home page.
- `_build_feed` redirects to `/login` when an anonymous user passes `?feed=following`. This is a server-side redirect, not a template guard.
- HTMX requests get `partials/feed_content.html` instead of `articles/home.html`. The partial is a fragment of the same feed UI; full-page loads and HTMX tab-swaps both render the same feed code path.
- `Article.save()` regenerates the slug **only if `self.pk is None`** — editing the title of a published article does not change its URL.

## Dependencies

- **Uses**: `helpers.pagination.paginate`, `helpers.htmx.is_htmx`, `taggit` (3rd-party), `markdown` + `nh3` (in templatetag).
- **Used by**: `comments` (imports `Article`), `accounts` (imports only `profile_view`, no model or query access).
