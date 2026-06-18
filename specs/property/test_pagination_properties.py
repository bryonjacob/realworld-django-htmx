"""Property tests for the article/feed pagination invariants.

Binds the @property-based PAGINATION-* scenarios in
docs/specs/articles/domain/article-properties.feature to Hypothesis via
pytest-bdd-property. They exercise helpers.pagination.paginate directly — the
pure function the feed machinery delegates paging to.

(SLUG-003 in the same feature file is bound separately in
test_slug_properties.py, which needs the Django ORM.)
"""

from django.test import RequestFactory
from hypothesis import strategies as st
from pytest_bdd import scenario
from pytest_bdd_property import property_then, property_when, register_strategy

from helpers.pagination import DEFAULT_PER_PAGE, paginate

_rf = RequestFactory()

_FEATURE = "../../docs/specs/articles/domain/article-properties.feature"

# Bind only the DB-free pagination properties by name. SLUG-003 in the same
# feature file is DB-backed and covered by a hypothesis.extra.django test in the
# Django suite, so it is deliberately NOT collected here (binding it with no
# steps would pass vacuously).


@scenario(_FEATURE, "Any page request resolves to a page of one or more")
def test_pagination_003():
    pass


@scenario(_FEATURE, "A page never holds more articles than the page size")
def test_pagination_004():
    pass


@scenario(_FEATURE, "The reported page range always contains at least one page")
def test_pagination_005():
    pass


class _FakeQuerySet:
    """List-backed queryset supporting the slice + count paginate() needs."""

    def __init__(self, n: int):
        self._items = list(range(n))

    def count(self) -> int:
        return len(self._items)

    def __getitem__(self, s):
        return self._items[s]


# "any article collection <C>" -> 0..50 articles. Includes the empty collection,
# which is what PAGINATION-005 ("including none at all") relies on.
register_strategy("article collection", lambda: st.integers(min_value=0, max_value=50).map(_FakeQuerySet))
# "any page number <N>" -> arbitrary int, including out-of-range and negatives.
register_strategy("page number", lambda: st.integers(min_value=-5, max_value=60))


@property_when(r"<(\w+)> is paginated with the page value \"(.*)\" producing <(\w+)>")
def paginate_with_value(vals, results, qs_var, requested, out_var):
    results[out_var] = paginate(vals[qs_var], _rf.get("/", {"page": requested}))


@property_when(r"<(\w+)> is paginated at page <(\w+)> producing <(\w+)>")
def paginate_at_page(vals, results, qs_var, page_var, out_var):
    results[out_var] = paginate(vals[qs_var], _rf.get("/", {"page": str(vals[page_var])}))


@property_when(r"<(\w+)> is paginated producing <(\w+)>")
def paginate_plain(vals, results, qs_var, out_var):
    results[out_var] = paginate(vals[qs_var], _rf.get("/"))


@property_then(r"<(\w+)> responds successfully")
def responds_successfully(vals, results, out_var):
    assert results[out_var] is not None


@property_then(r"the resolved page number of <(\w+)> is at least 1")
def page_at_least_one(vals, results, out_var):
    assert results[out_var].page >= 1


@property_then(r"<(\w+)> holds at most ten articles")
def at_most_ten(vals, results, out_var):
    assert len(results[out_var].items) <= DEFAULT_PER_PAGE


@property_then(r"the reported page range of <(\w+)> contains at least one page")
def range_at_least_one(vals, results, out_var):
    assert len(results[out_var].pages) >= 1
