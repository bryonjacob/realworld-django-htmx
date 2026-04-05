from dataclasses import dataclass

from django.db.models import QuerySet
from django.http import HttpRequest

DEFAULT_PER_PAGE = 10


@dataclass
class Page:
    items: list
    page: int
    pages: range


def paginate(
    queryset: QuerySet,
    request: HttpRequest,
    per_page: int = DEFAULT_PER_PAGE,
) -> Page:
    """Paginate queryset by ?page= query param.

    Invalid / missing / non-positive page defaults to 1, matching the
    behavior the e2e suite relies on (commit 48d39f8). Django's built-in
    Paginator raises on invalid input and is deliberately not used here.
    """
    try:
        page = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page = 1
    page = max(1, page)
    offset = (page - 1) * per_page
    total = queryset.count()
    items = list(queryset[offset : offset + per_page])
    total_pages = max(1, (total + per_page - 1) // per_page)
    return Page(items=items, page=page, pages=range(1, total_pages + 1))
