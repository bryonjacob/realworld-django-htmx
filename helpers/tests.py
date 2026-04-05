"""
Targeted unit tests for helpers with non-trivial logic.

Everything else — views, forms, models, templates — is also covered by the
per-app tests.py files and by the RealWorld e2e suite (just integration-test).
"""

from sqlite3 import IntegrityError as SQLiteIntegrityError
from unittest import TestCase as PlainTestCase
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.http import Http404
from django.test import RequestFactory, TestCase

from helpers import exceptions as exceptions_module
from helpers.context_processors import conduit_context
from helpers.exceptions import ResourceNotFound, clean_integrity_error, get_or_404
from helpers.htmx import is_htmx
from helpers.pagination import paginate

User = get_user_model()


class CleanIntegrityErrorTest(PlainTestCase):
    def test_sqlite_unique_violation_email(self):
        cause = SQLiteIntegrityError("UNIQUE constraint failed: accounts_user.email")
        error = IntegrityError()
        error.__cause__ = cause
        self.assertEqual(clean_integrity_error(error), "email")

    def test_sqlite_unique_violation_username(self):
        cause = SQLiteIntegrityError("UNIQUE constraint failed: accounts_user.username")
        error = IntegrityError()
        error.__cause__ = cause
        self.assertEqual(clean_integrity_error(error), "username")

    def test_returns_none_when_cause_is_none(self):
        error = IntegrityError()
        error.__cause__ = None
        self.assertIsNone(clean_integrity_error(error))

    def test_returns_none_for_unknown_cause_type(self):
        """Non-None cause that matches neither SQLite nor psycopg2 branches."""
        error = IntegrityError()
        error.__cause__ = ValueError("something else entirely")
        self.assertIsNone(clean_integrity_error(error))

    def test_returns_none_for_malformed_sqlite_message(self):
        cause = SQLiteIntegrityError("something unexpected")
        error = IntegrityError()
        error.__cause__ = cause
        self.assertIsNone(clean_integrity_error(error))

    def test_psycopg2_unique_violation(self):
        """Cover the psycopg2 UniqueViolation branch via a fake exception class."""

        class FakeUniqueViolation(Exception):
            pass

        cause = FakeUniqueViolation("duplicate key value violates unique constraint: Key (email)=(a@b.com)")
        error = IntegrityError()
        error.__cause__ = cause
        with patch.object(exceptions_module, "UniqueViolation", FakeUniqueViolation):
            self.assertEqual(clean_integrity_error(error), "email")

    def test_psycopg2_unique_violation_malformed(self):
        """Cover the `except Exception` fallback when psycopg2-style parsing fails."""

        class FakeUniqueViolation(Exception):
            pass

        cause = FakeUniqueViolation("totally unparseable")
        error = IntegrityError()
        error.__cause__ = cause
        with patch.object(exceptions_module, "UniqueViolation", FakeUniqueViolation):
            self.assertIsNone(clean_integrity_error(error))


class GetOr404Test(TestCase):
    def test_returns_object_when_found(self):
        user = User.objects.create_user(email="a@b.com", username="alice", password="pw")
        result = get_or_404(User, "user", username="alice")
        self.assertEqual(result, user)

    def test_raises_resource_not_found_when_missing(self):
        with self.assertRaises(ResourceNotFound) as ctx:
            get_or_404(User, "user", username="ghost")
        self.assertEqual(ctx.exception.resource, "user")
        self.assertIsInstance(ctx.exception, Http404)


class ResourceNotFoundTest(PlainTestCase):
    def test_message_includes_resource_name(self):
        err = ResourceNotFound("article")
        self.assertEqual(err.resource, "article")
        self.assertIn("article not found", str(err))


class IsHtmxTest(PlainTestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_true_when_header_set(self):
        request = self.rf.get("/", HTTP_HX_REQUEST="true")
        self.assertTrue(is_htmx(request))

    def test_false_when_header_missing(self):
        self.assertFalse(is_htmx(self.rf.get("/")))

    def test_false_when_header_is_false(self):
        self.assertFalse(is_htmx(self.rf.get("/", HTTP_HX_REQUEST="false")))


class ConduitContextTest(PlainTestCase):
    def test_anonymous_user(self):
        request = MagicMock()
        request.user = AnonymousUser()
        ctx = conduit_context(request)
        self.assertEqual(ctx["conduit_user_json"], "null")
        self.assertFalse(ctx["conduit_authenticated"])

    def test_authenticated_user_with_bio_and_image(self):
        user = MagicMock()
        user.is_authenticated = True
        user.username = "alice"
        user.email = "alice@x.com"
        user.bio = "hello"
        user.image = "http://img"
        request = MagicMock(user=user)
        ctx = conduit_context(request)
        self.assertTrue(ctx["conduit_authenticated"])
        self.assertIn("alice", ctx["conduit_user_json"])
        self.assertIn("hello", ctx["conduit_user_json"])

    def test_authenticated_user_with_empty_bio_and_image(self):
        user = MagicMock()
        user.is_authenticated = True
        user.username = "bob"
        user.email = "b@x.com"
        user.bio = ""
        user.image = ""
        request = MagicMock(user=user)
        ctx = conduit_context(request)
        self.assertIn('"bio": null', ctx["conduit_user_json"])
        self.assertIn('"image": null', ctx["conduit_user_json"])


class PaginateTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = User.objects.create_user(email="p@b.com", username="paginator", password="pw")
        from articles.models import Article

        cls.Article = Article
        for i in range(25):
            Article.objects.create(author=author, title=f"t{i:02d}", summary="s", content="c")

    def setUp(self):
        self.rf = RequestFactory()
        self.qs = self.Article.objects.all().order_by("title")

    def test_happy_path(self):
        result = paginate(self.qs, self.rf.get("/", {"page": "2"}))
        self.assertEqual(len(result.items), 10)
        self.assertEqual([a.title for a in result.items], [f"t{i:02d}" for i in range(10, 20)])
        self.assertEqual(result.page, 2)
        self.assertEqual(result.pages, range(1, 4))

    def test_invalid_page_string_defaults_to_one(self):
        result = paginate(self.qs, self.rf.get("/", {"page": "abc"}))
        self.assertEqual(result.page, 1)
        self.assertEqual(len(result.items), 10)
        self.assertEqual(result.items[0].title, "t00")

    def test_page_zero_clamped_to_one(self):
        result = paginate(self.qs, self.rf.get("/", {"page": "0"}))
        self.assertEqual(result.page, 1)
        self.assertEqual(len(result.items), 10)
        self.assertEqual(result.items[0].title, "t00")

    def test_page_beyond_range_returns_empty_items(self):
        small_qs = self.qs.filter(title__in=["t00", "t01", "t02", "t03", "t04"])
        result = paginate(small_qs, self.rf.get("/", {"page": "99"}))
        self.assertEqual(result.items, [])
        self.assertEqual(result.page, 99)
        self.assertEqual(result.pages, range(1, 2))

    def test_empty_queryset_still_has_one_page(self):
        empty_qs = self.Article.objects.filter(title="does-not-exist")
        result = paginate(empty_qs, self.rf.get("/"))
        self.assertEqual(result.items, [])
        self.assertEqual(result.page, 1)
        self.assertEqual(result.pages, range(1, 2))

    def test_missing_page_param_defaults_to_one(self):
        result = paginate(self.qs, self.rf.get("/"))
        self.assertEqual(result.page, 1)
        self.assertEqual(len(result.items), 10)
        self.assertEqual(result.pages, range(1, 4))
