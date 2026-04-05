"""Unit tests for articles app — views, models, template tags, management command."""

from io import StringIO
from typing import cast

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse

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

    def test_new_article_defaults_to_published_with_timestamp(self):
        user = make_user()
        a = Article.objects.create(author=user, title="Pub", summary="s", content="c")
        self.assertTrue(a.is_published)
        self.assertIsNotNone(a.published_at)

    def test_draft_has_no_published_at(self):
        user = make_user()
        a = Article.objects.create(author=user, title="Draft", summary="s", content="c", is_published=False)
        self.assertFalse(a.is_published)
        self.assertIsNone(a.published_at)

    def test_publishing_a_draft_stamps_published_at(self):
        user = make_user()
        a = Article.objects.create(author=user, title="Later", summary="s", content="c", is_published=False)
        self.assertIsNone(a.published_at)
        a.is_published = True
        a.save()
        self.assertIsNotNone(a.published_at)

    def test_republishing_does_not_change_published_at(self):
        user = make_user()
        a = Article.objects.create(author=user, title="Stable", summary="s", content="c")
        original = a.published_at
        a.is_published = False
        a.save()
        a.is_published = True
        a.save()
        self.assertEqual(a.published_at, original)

    def test_visible_to_anonymous_hides_drafts(self):
        from django.contrib.auth.models import AnonymousUser

        alice = make_user()
        Article.objects.create(author=alice, title="Public", summary="", content="")
        Article.objects.create(author=alice, title="Private", summary="", content="", is_published=False)
        titles = set(Article.objects.visible_to(AnonymousUser()).values_list("title", flat=True))
        self.assertEqual(titles, {"Public"})

    def test_visible_to_author_includes_own_drafts(self):
        alice = make_user()
        bob = make_user(email="bob@x.com", username="bob")
        Article.objects.create(author=alice, title="Alice Public", summary="", content="")
        Article.objects.create(author=alice, title="Alice Draft", summary="", content="", is_published=False)
        Article.objects.create(author=bob, title="Bob Draft", summary="", content="", is_published=False)
        titles = set(Article.objects.visible_to(alice).values_list("title", flat=True))
        self.assertEqual(titles, {"Alice Public", "Alice Draft"})


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

    def test_drafts_hidden_from_global_feed(self):
        make_article(self.alice, title="Draft One")
        Article.objects.filter(title="Draft One").update(is_published=False)
        resp = self.client.get(reverse("home"))
        self.assertNotContains(resp, "Draft One")

    def test_drafts_hidden_from_global_feed_for_author(self):
        cache.clear()
        make_article(self.alice, title="My Draft")
        Article.objects.filter(title="My Draft").update(is_published=False)
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("home"))
        self.assertNotContains(resp, "My Draft")

    def test_drafts_hidden_from_tag_feed(self):
        make_article(self.alice, title="Draft Tag", tags=["secret"])
        Article.objects.filter(title="Draft Tag").update(is_published=False)
        resp = self.client.get(reverse("tag", args=["secret"]))
        self.assertNotContains(resp, "Draft Tag")

    def test_tag_cache_excludes_draft_only_tags(self):
        cache.clear()
        a = make_article(self.alice, title="Only Draft", tags=["drafty"])
        Article.objects.filter(pk=a.pk).update(is_published=False)
        resp = self.client.get(reverse("home"))
        tag_names = [t.name for t in resp.context["tags"]]
        self.assertNotIn("drafty", tag_names)
        self.assertIn("python", tag_names)


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

    def test_draft_detail_404_for_anonymous(self):
        Article.objects.filter(pk=self.article.pk).update(is_published=False)
        resp = self.client.get(reverse("article_detail", args=[self.article.slug]))
        self.assertEqual(resp.status_code, 404)

    def test_draft_detail_404_for_other_user(self):
        Article.objects.filter(pk=self.article.pk).update(is_published=False)
        self.client.force_login(self.bob)
        resp = self.client.get(reverse("article_detail", args=[self.article.slug]))
        self.assertEqual(resp.status_code, 404)

    def test_draft_detail_visible_to_author(self):
        Article.objects.filter(pk=self.article.pk).update(is_published=False)
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("article_detail", args=[self.article.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Detail Me")


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

    def test_post_with_draft_action_creates_draft(self):
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("article_create"),
            {"title": "Secret", "description": "", "body": "", "tags": "", "action": "draft"},
        )
        self.assertEqual(resp.status_code, 302)
        art = Article.objects.get(title="Secret")
        self.assertFalse(art.is_published)
        self.assertIsNone(art.published_at)

    def test_post_with_publish_action_creates_published(self):
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("article_create"),
            {"title": "Loud", "description": "", "body": "", "tags": "", "action": "publish"},
        )
        self.assertEqual(resp.status_code, 302)
        art = Article.objects.get(title="Loud")
        self.assertTrue(art.is_published)
        self.assertIsNotNone(art.published_at)

    def test_editor_shows_save_as_draft_button_on_create(self):
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("article_create"))
        self.assertContains(resp, "Save as Draft")
        self.assertContains(resp, "Publish Article")


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

    def test_editing_published_article_ignores_draft_action(self):
        # Safety net: even if someone POSTs action=draft against a
        # published article, it stays published — the editor UI hides the
        # button, and the view refuses to unpublish via the editor path.
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("article_edit", args=[self.article.slug]),
            {"title": "Edit Me", "description": "d", "body": "b", "tags": "", "action": "draft"},
        )
        self.assertEqual(resp.status_code, 302)
        self.article.refresh_from_db()
        self.assertTrue(self.article.is_published)

    def test_editing_a_draft_with_publish_action_publishes(self):
        Article.objects.filter(pk=self.article.pk).update(is_published=False, published_at=None)
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("article_edit", args=[self.article.slug]),
            {"title": "Edit Me", "description": "d", "body": "b", "tags": "", "action": "publish"},
        )
        self.assertEqual(resp.status_code, 302)
        self.article.refresh_from_db()
        self.assertTrue(self.article.is_published)
        self.assertIsNotNone(self.article.published_at)

    def test_editing_a_draft_with_draft_action_keeps_draft(self):
        Article.objects.filter(pk=self.article.pk).update(is_published=False, published_at=None)
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("article_edit", args=[self.article.slug]),
            {"title": "Edit Me", "description": "d", "body": "b", "tags": "", "action": "draft"},
        )
        self.assertEqual(resp.status_code, 302)
        self.article.refresh_from_db()
        self.assertFalse(self.article.is_published)

    def test_editor_hides_save_as_draft_for_published_article(self):
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("article_edit", args=[self.article.slug]))
        self.assertNotContains(resp, "Save as Draft")
        self.assertContains(resp, "Publish Article")

    def test_editor_shows_save_as_draft_for_draft(self):
        Article.objects.filter(pk=self.article.pk).update(is_published=False, published_at=None)
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("article_edit", args=[self.article.slug]))
        self.assertContains(resp, "Save as Draft")
        self.assertContains(resp, "Publish Article")


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

    def test_cannot_favorite_a_draft(self):
        Article.objects.filter(pk=self.article.pk).update(is_published=False)
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("article_favorite", args=[self.article.slug]))
        self.assertEqual(resp.status_code, 404)


class ArticlePublishViewTest(TestCase):
    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(email="bob@x.com", username="bob")
        self.article = make_article(self.alice, title="Toggle Me")

    def test_anonymous_redirects(self):
        resp = self.client.post(reverse("article_publish", args=[self.article.slug]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", cast(HttpResponseRedirect, resp).url)

    def test_non_author_gets_404(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("article_publish", args=[self.article.slug]), {"action": "unpublish"})
        self.assertEqual(resp.status_code, 404)

    def test_author_unpublishes_published_article(self):
        self.client.force_login(self.alice)
        resp = self.client.post(reverse("article_publish", args=[self.article.slug]), {"action": "unpublish"})
        self.assertRedirects(resp, reverse("article_detail", args=[self.article.slug]))
        self.article.refresh_from_db()
        self.assertFalse(self.article.is_published)

    def test_author_publishes_draft_and_stamps_published_at(self):
        Article.objects.filter(pk=self.article.pk).update(is_published=False, published_at=None)
        self.client.force_login(self.alice)
        resp = self.client.post(reverse("article_publish", args=[self.article.slug]), {"action": "publish"})
        self.assertRedirects(resp, reverse("article_detail", args=[self.article.slug]))
        self.article.refresh_from_db()
        self.assertTrue(self.article.is_published)
        self.assertIsNotNone(self.article.published_at)

    def test_unpublish_preserves_comments_and_favorites(self):
        from comments.models import Comment

        self.article.favorites.add(self.bob)
        Comment.objects.create(article=self.article, author=self.bob, content="nice post")
        self.client.force_login(self.alice)
        self.client.post(reverse("article_publish", args=[self.article.slug]), {"action": "unpublish"})
        self.article.refresh_from_db()
        self.assertEqual(self.article.favorites.count(), 1)
        self.assertEqual(self.article.comment_set.count(), 1)

    def test_draft_detail_hides_comments_and_shows_banner(self):
        Article.objects.filter(pk=self.article.pk).update(is_published=False)
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("article_detail", args=[self.article.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "only you can see this")
        self.assertNotContains(resp, 'name="body"')  # comment textarea hidden
        self.assertContains(resp, "Publish Article")  # publish button visible


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
