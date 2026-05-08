"""Unit tests for articles app — views, models, template tags, management command."""

import tempfile
from contextlib import ExitStack
from io import StringIO
from pathlib import Path
from typing import cast

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.test import TestCase, override_settings
from django.urls import reverse

from articles import search
from articles.models import Article
from articles.templatetags.markdown_filter import render_markdown

User = get_user_model()


def make_user(email="alice@example.com", username="alice", password="pw123456", **extra):
    return User.objects.create_user(email=email, username=username, password=password, **extra)


def make_article(author, title="A Post", summary="s", content="c", tags=()):
    a = Article.objects.create(author=author, title=title, summary=summary, content=content)
    for t in tags:
        a.tags.add(t)
    return a


class ArticleModelTest(TestCase):
    def test_save_generates_slug_on_create(self):
        user = make_user()
        a = Article.objects.create(author=user, title="Hello World", summary="s", content="c")
        self.assertEqual(a.slug, "hello-world")

    def test_save_does_not_regenerate_slug_on_update(self):
        user = make_user()
        a = Article.objects.create(author=user, title="Hello World", summary="s", content="c")
        original_slug = a.slug
        a.title = "Totally Different Title"
        a.save()
        self.assertEqual(a.slug, original_slug)

    def test_with_favorites_anonymous_sets_is_favorite_false(self):
        from django.contrib.auth.models import AnonymousUser

        user = make_user()
        make_article(user)
        qs = Article.objects.with_favorites(AnonymousUser())
        for art in qs:
            self.assertFalse(art.is_favorite)

    def test_with_favorites_authenticated_reflects_favorites(self):
        alice = make_user()
        bob = make_user(email="bob@x.com", username="bob")
        a = make_article(alice)
        a.favorites.add(bob)
        qs = Article.objects.with_favorites(bob)
        art = qs.get(pk=a.pk)
        self.assertTrue(art.is_favorite)
        self.assertEqual(art.num_favorites, 1)


class MarkdownFilterTest(TestCase):
    def test_renders_markdown_and_sanitizes(self):
        html = render_markdown("# Hello\n\n**bold**")
        self.assertIn("<h1>", html)
        self.assertIn("<strong>", html)

    def test_strips_unsafe_html(self):
        html = render_markdown("<script>alert(1)</script>ok")
        self.assertNotIn("<script>", html)


class HomeViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.alice = make_user()
        self.bob = make_user(email="bob@x.com", username="bob")
        self.art1 = make_article(self.alice, title="Post One", tags=["python"])
        self.art2 = make_article(self.bob, title="Post Two", tags=["django"])

    def test_anonymous_home_shows_all(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Post One")
        self.assertContains(resp, "Post Two")
        self.assertEqual(resp.context["active_tab"], "global")

    def test_tag_query_filters(self):
        resp = self.client.get(reverse("home") + "?tag=python")
        self.assertContains(resp, "Post One")
        self.assertNotContains(resp, "Post Two")
        self.assertEqual(resp.context["active_tab"], "tag")

    def test_tag_url_path_filters(self):
        resp = self.client.get(reverse("tag", args=["django"]))
        self.assertContains(resp, "Post Two")
        self.assertNotContains(resp, "Post One")

    def test_following_feed_anonymous_redirects_to_login(self):
        resp = self.client.get(reverse("home") + "?feed=following")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", cast(HttpResponseRedirect, resp).url)

    def test_following_feed_authenticated(self):
        self.alice.followers.add(self.bob)  # bob follows alice
        self.client.force_login(self.bob)
        resp = self.client.get(reverse("home") + "?feed=following")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Post One")
        self.assertNotContains(resp, "Post Two")
        self.assertEqual(resp.context["active_tab"], "following")

    def test_invalid_page_defaults_to_one(self):
        resp = self.client.get(reverse("home") + "?page=bogus")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["page"], 1)

    def test_htmx_request_returns_partial(self):
        resp = self.client.get(reverse("home"), HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("partials/feed_content.html", [t.name for t in resp.templates if t.name])


class ArticleDetailViewTest(TestCase):
    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(email="bob@x.com", username="bob")
        self.article = make_article(self.alice, title="Detail Me")

    def test_unknown_slug_returns_404(self):
        resp = self.client.get(reverse("article_detail", args=["does-not-exist"]))
        self.assertEqual(resp.status_code, 404)

    def test_detail_renders(self):
        resp = self.client.get(reverse("article_detail", args=[self.article.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Detail Me")

    def test_detail_authenticated_shows_following_flag(self):
        self.alice.followers.add(self.bob)
        self.client.force_login(self.bob)
        resp = self.client.get(reverse("article_detail", args=[self.article.slug]))
        self.assertTrue(resp.context["is_following"])


class ArticleCreateViewTest(TestCase):
    def setUp(self):
        self.alice = make_user()

    def test_anonymous_redirects(self):
        resp = self.client.get(reverse("article_create"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", cast(HttpResponseRedirect, resp).url)

    def test_get_renders_form(self):
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("article_create"))
        self.assertEqual(resp.status_code, 200)

    def test_post_creates_article_with_tags(self):
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("article_create"),
            {"title": "New Title", "description": "d", "body": "b", "tags": "python,  django  , "},
        )
        self.assertEqual(resp.status_code, 302)
        art = Article.objects.get(title="New Title")
        self.assertEqual(art.author, self.alice)
        self.assertEqual(art.summary, "d")
        self.assertEqual(art.content, "b")
        self.assertEqual(sorted(t.name for t in art.tags.all()), ["django", "python"])

    def test_post_creates_article_without_tags(self):
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("article_create"),
            {"title": "No Tags", "description": "", "body": "", "tags": ""},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Article.objects.get(title="No Tags").tags.count(), 0)

    def test_post_invalid_form_rerenders(self):
        self.client.force_login(self.alice)
        resp = self.client.post(reverse("article_create"), {"title": "", "description": "", "body": "", "tags": ""})
        self.assertEqual(resp.status_code, 200)


class ArticleEditViewTest(TestCase):
    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(email="bob@x.com", username="bob")
        self.article = make_article(self.alice, title="Edit Me", tags=["python"])

    def test_non_author_gets_404(self):
        self.client.force_login(self.bob)
        resp = self.client.get(reverse("article_edit", args=[self.article.slug]))
        self.assertEqual(resp.status_code, 404)

    def test_get_prefills_form(self):
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("article_edit", args=[self.article.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Edit Me")
        self.assertContains(resp, "python")

    def test_post_updates_article(self):
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("article_edit", args=[self.article.slug]),
            {"title": "Edit Me", "description": "new desc", "body": "new body", "tags": "rust"},
        )
        self.assertEqual(resp.status_code, 302)
        self.article.refresh_from_db()
        self.assertEqual(self.article.summary, "new desc")
        self.assertEqual(self.article.content, "new body")
        self.assertEqual([t.name for t in self.article.tags.all()], ["rust"])

    def test_post_invalid_form_rerenders(self):
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("article_edit", args=[self.article.slug]),
            {"title": "", "description": "", "body": "", "tags": ""},
        )
        self.assertEqual(resp.status_code, 200)


class ArticleDeleteViewTest(TestCase):
    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(email="bob@x.com", username="bob")
        self.article = make_article(self.alice, title="Delete Me")

    def test_non_author_gets_404(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("article_delete", args=[self.article.slug]))
        self.assertEqual(resp.status_code, 404)

    def test_author_can_delete(self):
        self.client.force_login(self.alice)
        resp = self.client.post(reverse("article_delete", args=[self.article.slug]))
        self.assertRedirects(resp, reverse("home"))
        self.assertFalse(Article.objects.filter(slug=self.article.slug).exists())


class ArticleFavoriteViewTest(TestCase):
    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(email="bob@x.com", username="bob")
        self.article = make_article(self.alice, title="Fav Me")

    def test_anonymous_redirects(self):
        resp = self.client.post(reverse("article_favorite", args=[self.article.slug]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", cast(HttpResponseRedirect, resp).url)

    def test_toggle_favorite_on_and_off(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("article_favorite", args=[self.article.slug]))
        self.assertRedirects(resp, reverse("article_detail", args=[self.article.slug]))
        self.assertTrue(self.article.favorites.filter(pk=self.bob.pk).exists())

        resp = self.client.post(reverse("article_favorite", args=[self.article.slug]))
        self.assertFalse(self.article.favorites.filter(pk=self.bob.pk).exists())

    def test_htmx_returns_partial(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("article_favorite", args=[self.article.slug]), HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)

    def test_unknown_slug_404(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("article_favorite", args=["ghost"]))
        self.assertEqual(resp.status_code, 404)


class SeedDataCommandTest(TestCase):
    def test_seed_data_creates_users_and_articles(self):
        out = StringIO()
        call_command("seed_data", stdout=out)
        self.assertTrue(User.objects.filter(username="johndoe").exists())
        self.assertTrue(User.objects.filter(username="janedoe").exists())
        self.assertEqual(Article.objects.filter(author__username="johndoe").count(), 5)
        self.assertEqual(Article.objects.filter(author__username="janedoe").count(), 3)
        self.assertIn("Seed data created successfully.", out.getvalue())

    def test_seed_data_is_idempotent(self):
        call_command("seed_data", stdout=StringIO())
        out = StringIO()
        call_command("seed_data", stdout=out)
        self.assertIn("Seed data already exists", out.getvalue())


class CreateUserCommandTest(TestCase):
    def test_create_user_success(self):
        out = StringIO()
        call_command("createUser", "--email=c@x.com", "--username=charlie", "--password=pw123456", stdout=out)
        self.assertTrue(User.objects.filter(username="charlie").exists())
        self.assertIn("User created successfully.", out.getvalue())

    def test_create_user_already_exists(self):
        make_user(email="c@x.com", username="charlie")
        out = StringIO()
        call_command("createUser", "--email=c@x.com", "--username=charlie", "--password=pw123456", stdout=out)
        self.assertIn("User already exists.", out.getvalue())

    def test_create_user_missing_args(self):
        out = StringIO()
        call_command("createUser", stdout=out)
        self.assertIn("Please provide", out.getvalue())


def _make_search_article(**overrides) -> Article:
    """Create an Article with a fresh User. Used by SearchModuleTests."""
    username = overrides.pop("username", "alice")
    author = User.objects.create_user(username=username, email=f"{username}@x.test", password="pw123456")
    defaults = {"title": "Hello Django", "summary": "A post about web", "content": "Django is a web framework"}
    defaults.update(overrides)
    return Article.objects.create(author=author, **defaults)


class SearchModuleTests(TestCase):
    def setUp(self):
        self._stack = ExitStack()
        tmp = self._stack.enter_context(tempfile.TemporaryDirectory())
        self._stack.enter_context(override_settings(SEARCH_INDEX_DIR=tmp))
        self.addCleanup(self._stack.close)

    def test_query_empty_string_returns_empty_list(self):
        self.assertEqual(search.query_ids(""), [])
        self.assertEqual(search.query_ids("   "), [])

    def test_index_then_query_finds_article(self):
        a = _make_search_article(title="Django HTMX patterns")
        search.index_article(a)
        self.assertEqual(search.query_ids("django"), [a.pk])

    def test_title_outranks_content(self):
        a1 = _make_search_article(username="u1", title="Cooking", summary="x", content="django appears here")
        a2 = _make_search_article(username="u2", title="Django guide", summary="y", content="cooking appears here")
        search.index_article(a1)
        search.index_article(a2)
        self.assertEqual(search.query_ids("django"), [a2.pk, a1.pk])

    def test_deindex_removes_from_results(self):
        a = _make_search_article(title="Removable")
        search.index_article(a)
        self.assertEqual(search.query_ids("removable"), [a.pk])
        search.deindex_article(a.pk)
        self.assertEqual(search.query_ids("removable"), [])

    def test_deindex_missing_id_is_noop(self):
        # Must not raise even when nothing matches.
        search.deindex_article(99999)

    def test_query_no_matches_returns_empty(self):
        a = _make_search_article(title="Hello world")
        search.index_article(a)
        self.assertEqual(search.query_ids("nonexistentword"), [])

    def test_get_index_creates_directory(self):
        with tempfile.TemporaryDirectory() as parent:
            sub = Path(parent) / "deeply" / "nested"
            with override_settings(SEARCH_INDEX_DIR=sub):
                ix = search.get_index()
                self.assertTrue(sub.exists())
                self.assertIsNotNone(ix)

    def test_get_index_reopens_existing(self):
        # First call creates; second call must reopen rather than recreate.
        a = _make_search_article(title="Persisted")
        search.index_article(a)
        # New get_index() call goes through the open_dir branch.
        ix = search.get_index()
        self.assertIsNotNone(ix)
        self.assertEqual(search.query_ids("persisted"), [a.pk])

    def test_reindex_all_rebuilds_from_db(self):
        a1 = _make_search_article(username="u1", title="First")
        a2 = _make_search_article(username="u2", title="Second")
        # Don't call index_article — verify reindex_all picks them up from the DB.
        search.reindex_all()
        self.assertEqual(search.query_ids("first"), [a1.pk])
        self.assertEqual(search.query_ids("second"), [a2.pk])

    def test_update_document_replaces_existing(self):
        a = _make_search_article(title="Original Title")
        search.index_article(a)
        a.title = "Replaced Title"
        a.save()
        search.index_article(a)
        self.assertEqual(search.query_ids("original"), [])
        self.assertEqual(search.query_ids("replaced"), [a.pk])

    def test_query_ids_returns_list_of_ints(self):
        a = _make_search_article(title="Typed")
        search.index_article(a)
        result = search.query_ids("typed")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], int)
