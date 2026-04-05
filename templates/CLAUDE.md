# templates/

Django templates. Split into full-page templates and HTMX partials.

## Layout

```
templates/
  base.html              # Root layout — navbar, footer, conduit JS bootstrap
  accounts/              # Full-page templates for the accounts app
    login.html
    register.html
    settings.html
    profile.html         # Used by articles.views.profile_view (not accounts/)
    profile_404.html
  articles/              # Full-page templates for the articles app
    home.html
    detail.html
    detail_404.html
    editor.html
  partials/              # HTMX fragment templates (rendered for HX-Request)
    header.html
    footer.html
    feed_content.html    # The feed portion of home.html — returned for HTMX feed swaps
    article_list.html    # List of article preview cards
    article_meta.html    # Author + date + favorite button for one article
    favorite_button.html # Just the favorite button (swap target)
    follow_button.html   # Just the follow button (swap target)
    comment_list.html    # Entire comment thread (swap target for create/delete)
```

## Conventions

- **Full-page templates** extend `base.html` and are rendered on normal (non-HTMX) requests.
- **Partials** are standalone fragments with no `{% extends %}`. They are returned when `is_htmx(request)` is true, and they are also `{% include %}`-ed by the full-page templates so there is a single source of truth.
- **Swap granularity is the partial**: if HTMX targets `#favorite-button`, the view returns `partials/favorite_button.html` and the server sends just the button. The full-page template also `{% include %}`s the same partial, so the first paint and subsequent swaps render identically.
- **`templates/accounts/profile.html` lives in `accounts/` but is rendered from `articles/views.py::profile_view`**. The template location matches the URL namespace, not the code location. This is intentional (see the `refactor-pass` epic) — don't move it.

## Selectors contract

The RealWorld e2e suite in `realworld/specs/e2e/SELECTORS.md` pins specific CSS classes, `name` attributes, and text strings. Before renaming any of the following, grep the SELECTORS contract:

- `<nav class="navbar">`, `<a class="navbar-brand">`, `<a class="nav-link">`
- `input[name="email"]`, `input[name="password"]`, `input[name="username"]`, `input[name="title"]`, `input[name="description"]`, `textarea[name="body"]`, `input[name="image"]`, `textarea[name="bio"]`
- Tab labels `Your Feed`, `Global Feed`, `My Articles`, `Favorited Articles`
- Button text `Sign in`, `Sign up`, `Publish Article`

Breaking these is how you get a working app that fails the e2e suite.
