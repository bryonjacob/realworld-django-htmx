"""Unit tests for articles app — views, models, template tags, management command."""

from io import StringIO
from typing import cast

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

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


class SlugStabilityPropertyTest(HypothesisTestCase):
    """RID-ARTICLES-SLUG-003: property — any title edit leaves the slug fixed.

    `Article.save()` only regenerates the slug when `self.pk is None`, so once an
    article is created its URL is stable no matter what the title is later set to.
    Each Hypothesis example runs in its own rolled-back transaction, so creating a
    fresh author + article per example is collision-free.
    """

    @given(new_title=st.text(min_size=1, max_size=140))
    def test_slug_never_changes_on_edit(self, new_title):
        author = User.objects.create_user(email="slug@example.com", username="sluggy", password="pw123456")
        article = Article.objects.create(author=author, title="Original Fixed Title", summary="s", content="c")
        original_slug = article.slug
        article.title = new_title
        article.save()
        self.assertEqual(article.slug, original_slug)


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

    def test_global_feed_orders_newest_first(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        articles = list(resp.context["articles"])
        self.assertEqual([a.pk for a in articles], [self.art2.pk, self.art1.pk])

    def test_full_page_load_renders_full_template(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("articles/home.html", [t.name for t in resp.templates if t.name])

    def test_feed_shows_at_most_ten_articles_per_page(self):
        for i in range(11):
            make_article(self.alice, title=f"Bulk Post {i}")
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["articles"]), 10)

    def test_feed_offers_all_tags(self):
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)
        tag_names = sorted(t.name for t in resp.context["tags"])
        self.assertEqual(tag_names, ["django", "python"])

    def test_new_tag_available_after_article_saved(self):
        # Prime the cache with the current tag set.
        self.client.get(reverse("home"))
        self.client.force_login(self.alice)
        self.client.post(
            reverse("article_create"),
            {"title": "Tagged Fresh", "description": "d", "body": "b", "tags": "rust"},
        )
        resp = self.client.get(reverse("home"))
        self.assertIn("rust", [t.name for t in resp.context["tags"]])


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

    def test_post_redirects_to_new_article_detail(self):
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("article_create"),
            {"title": "Land Here", "description": "d", "body": "b", "tags": ""},
        )
        art = Article.objects.get(title="Land Here")
        self.assertRedirects(resp, reverse("article_detail", args=[art.slug]))


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


class ProfileViewTest(TestCase):
    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(email="bob@x.com", username="bob")

    def test_articles_tab_lists_users_own_articles_newest_first(self):
        first = make_article(self.alice, title="Alice First")
        second = make_article(self.alice, title="Alice Second")
        make_article(self.bob, title="Bob Post")
        resp = self.client.get(reverse("profile", args=["alice"]))
        self.assertEqual(resp.status_code, 200)
        articles = list(resp.context["articles"])
        self.assertEqual([a.pk for a in articles], [second.pk, first.pk])
        self.assertEqual(resp.context["tab"], "my")

    def test_favorites_tab_lists_favorited_articles_newest_first(self):
        first = make_article(self.bob, title="Fav First")
        second = make_article(self.bob, title="Fav Second")
        make_article(self.bob, title="Unfavorited")
        first.favorites.add(self.alice)
        second.favorites.add(self.alice)
        resp = self.client.get(reverse("profile_favorites", args=["alice"]))
        self.assertEqual(resp.status_code, 200)
        articles = list(resp.context["articles"])
        self.assertEqual([a.pk for a in articles], [second.pk, first.pk])
        self.assertEqual(resp.context["tab"], "favorites")

    def test_unknown_username_returns_404(self):
        resp = self.client.get(reverse("profile", args=["ghost"]))
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
