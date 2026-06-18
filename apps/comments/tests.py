"""Unit tests for comments app — views."""

from typing import cast

from articles.models import Article
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse

from comments.models import Comment

User = get_user_model()


def make_user(email="alice@example.com", username="alice", password="pw123456", **extra):
    return User.objects.create_user(email=email, username=username, password=password, **extra)


class CommentCreateViewTest(TestCase):
    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(email="bob@x.com", username="bob")
        self.article = Article.objects.create(author=self.alice, title="Host", summary="s", content="c")

    def test_anonymous_redirects(self):
        resp = self.client.post(reverse("comment_create", args=[self.article.slug]), {"body": "hi"})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", cast(HttpResponseRedirect, resp).url)

    def test_empty_body_is_noop(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("comment_create", args=[self.article.slug]), {"body": "   "})
        self.assertEqual(Comment.objects.count(), 0)
        self.assertRedirects(resp, reverse("article_detail", args=[self.article.slug]))

    def test_create_comment(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("comment_create", args=[self.article.slug]), {"body": "great post"})
        self.assertRedirects(resp, reverse("article_detail", args=[self.article.slug]))
        self.assertEqual(Comment.objects.count(), 1)
        c = Comment.objects.get()
        self.assertEqual(c.author, self.bob)
        self.assertEqual(c.content, "great post")

    def test_htmx_returns_partial(self):
        self.client.force_login(self.bob)
        resp = self.client.post(
            reverse("comment_create", args=[self.article.slug]),
            {"body": "hello"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "hello")

    def test_unknown_article_404(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("comment_create", args=["ghost"]), {"body": "hi"})
        self.assertEqual(resp.status_code, 404)


class ArticleCommentListViewTest(TestCase):
    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(email="bob@x.com", username="bob")
        self.article = Article.objects.create(author=self.alice, title="Host", summary="s", content="c")

    def test_article_shows_all_its_comments(self):
        Comment.objects.create(article=self.article, author=self.bob, content="first comment")
        Comment.objects.create(article=self.article, author=self.alice, content="second comment")
        resp = self.client.get(reverse("article_detail", args=[self.article.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "first comment")
        self.assertContains(resp, "second comment")

    def test_article_with_no_comments(self):
        resp = self.client.get(reverse("article_detail", args=[self.article.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context["comments"]), [])


class CommentContentTrimTest(TestCase):
    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(email="bob@x.com", username="bob")
        self.article = Article.objects.create(author=self.alice, title="Host", summary="s", content="c")

    def test_surrounding_whitespace_is_stripped(self):
        self.client.force_login(self.bob)
        self.client.post(reverse("comment_create", args=[self.article.slug]), {"body": "   spaced out  \n"})
        c = Comment.objects.get()
        self.assertEqual(c.content, "spaced out")


class CommentModelTest(TestCase):
    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(email="bob@x.com", username="bob")
        self.article = Article.objects.create(author=self.alice, title="Host", summary="s", content="c")

    def test_comment_belongs_to_article_and_author(self):
        comment = Comment.objects.create(article=self.article, author=self.bob, content="hi")
        self.assertEqual(comment.article, self.article)
        self.assertEqual(comment.author, self.bob)

    def test_comment_has_content_and_timestamps(self):
        comment = Comment.objects.create(article=self.article, author=self.bob, content="hi")
        self.assertEqual(comment.content, "hi")
        self.assertIsNotNone(comment.created)
        self.assertIsNotNone(comment.updated)

    def test_comments_ordered_newest_first(self):
        old = Comment.objects.create(article=self.article, author=self.bob, content="old")
        new = Comment.objects.create(article=self.article, author=self.bob, content="new")
        comments = list(Comment.objects.filter(article=self.article).order_by("-created", "-id"))
        self.assertEqual(comments, [new, old])

    def test_deleting_article_deletes_its_comments(self):
        Comment.objects.create(article=self.article, author=self.bob, content="hi")
        self.article.delete()
        self.assertEqual(Comment.objects.count(), 0)

    def test_deleting_author_deletes_their_comments(self):
        Comment.objects.create(article=self.article, author=self.bob, content="hi")
        self.bob.delete()
        self.assertEqual(Comment.objects.count(), 0)


class CommentDeleteViewTest(TestCase):
    def setUp(self):
        self.alice = make_user()  # article author
        self.bob = make_user(email="bob@x.com", username="bob")  # comment author
        self.carol = make_user(email="carol@x.com", username="carol")  # stranger
        self.article = Article.objects.create(author=self.alice, title="Host", summary="s", content="c")
        self.comment = Comment.objects.create(article=self.article, author=self.bob, content="hi")

    def test_anonymous_redirects(self):
        resp = self.client.post(reverse("comment_delete", args=[self.article.slug, self.comment.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", cast(HttpResponseRedirect, resp).url)

    def test_comment_author_can_delete(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("comment_delete", args=[self.article.slug, self.comment.id]))
        self.assertRedirects(resp, reverse("article_detail", args=[self.article.slug]))
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_article_author_can_delete(self):
        self.client.force_login(self.alice)
        resp = self.client.post(reverse("comment_delete", args=[self.article.slug, self.comment.id]))
        self.assertRedirects(resp, reverse("article_detail", args=[self.article.slug]))
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_stranger_forbidden(self):
        self.client.force_login(self.carol)
        resp = self.client.post(reverse("comment_delete", args=[self.article.slug, self.comment.id]))
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_unknown_article_404(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("comment_delete", args=["ghost", self.comment.id]))
        self.assertEqual(resp.status_code, 404)

    def test_unknown_comment_404(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("comment_delete", args=[self.article.slug, 99999]))
        self.assertEqual(resp.status_code, 404)

    def test_htmx_delete_returns_partial(self):
        self.client.force_login(self.bob)
        resp = self.client.post(
            reverse("comment_delete", args=[self.article.slug, self.comment.id]),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)
