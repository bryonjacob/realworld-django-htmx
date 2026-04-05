# apps/comments

Article comments. Small app — one model, two views.

## Key components

- **models.py** — `Comment` with ForeignKeys to `Article` and `User`, plus `content`/`created`/`updated` fields. No custom manager.
- **views.py** — `comment_create_view` (POST, trims whitespace, ignores empty bodies) and `comment_delete_view` (POST, allows delete by comment author OR article author, returns 403 for anyone else).
- **urls.py** — `/article/<slug>/comment`, `/article/<slug>/comment/<id>/delete`.

## Non-obvious things

- **Never use `article.comment_set`** — use `Comment.objects.filter(article=article)` instead. Django's reverse-FK accessor `comment_set` isn't typed by `django-types`, and using it triggers `ty` warnings. This was changed in commit `0cb53f4`.
- Both views are HTMX-aware: they return `partials/comment_list.html` on HTMX requests and redirect to the article page on normal form posts.
- Comment deletion by the **article** author (not just the comment author) is a deliberate feature — it's tested in `tests.py::test_article_author_can_delete` and is part of the e2e suite.
- `comment_delete_view` returns `HttpResponseForbidden()` (not 404) for strangers — distinguishing "doesn't exist" from "you can't touch this". E2e tests rely on this.

## Dependencies

- **Uses**: `articles.models.Article`, `helpers.htmx.is_htmx`.
- **Used by**: nothing (comments is a leaf).
