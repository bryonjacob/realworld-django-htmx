"""Unit tests for accounts app — views, models, forms."""

from typing import cast
from unittest.mock import PropertyMock, patch

from articles.models import Article
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse

from accounts.models import User


def make_user(email="alice@example.com", username="alice", password="pw123456", **extra):
    return User.objects.create_user(email=email, username=username, password=password, **extra)


class UserManagerTest(TestCase):
    def test_create_user_sets_password(self):
        user = User.objects.create_user(email="a@b.com", username="u1", password="secret")
        self.assertTrue(user.check_password("secret"))
        self.assertFalse(user.has_usable_password() is False)

    def test_create_user_without_password_sets_unusable(self):
        user = User.objects.create_user(email="a@b.com", username="u1")
        self.assertFalse(user.has_usable_password())

    def test_create_superuser_sets_flags(self):
        u = User.objects.create_superuser(email="root@x.com", username="root", password="pw")
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_superuser)
        self.assertTrue(u.is_active)

    def test_create_superuser_rejects_is_staff_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(email="r@x.com", username="r", password="pw", is_staff=False)

    def test_create_superuser_rejects_is_superuser_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(email="r@x.com", username="r", password="pw", is_superuser=False)


class UserModelTest(TestCase):
    def test_get_full_name_and_short_name_return_username(self):
        user = make_user()
        self.assertEqual(user.get_full_name(), "alice")
        self.assertEqual(user.get_short_name(), "alice")

    def test_is_following_when_not_authenticated_returns_false(self):
        """Cover the `else False` branch: is_following short-circuits when is_authenticated is False."""
        target = make_user()
        unauth_user = User(username="ghost", email="g@x.com")
        with patch.object(User, "is_authenticated", new_callable=PropertyMock, return_value=False):
            self.assertFalse(unauth_user.is_following(target))

    def test_is_following_true_and_false(self):
        alice = make_user()
        bob = make_user(email="bob@x.com", username="bob")
        self.assertFalse(alice.is_following(bob))
        bob.followers.add(alice)
        self.assertTrue(alice.is_following(bob))


class LoginViewTest(TestCase):
    def test_get_renders_form(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "form")

    def test_post_valid_credentials_logs_in_and_redirects(self):
        make_user()
        resp = self.client.post(reverse("login"), {"email": "alice@example.com", "password": "pw123456"})
        self.assertRedirects(resp, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), User.objects.get(username="alice").pk)

    def test_post_invalid_credentials_shows_error(self):
        make_user()
        resp = self.client.post(reverse("login"), {"email": "alice@example.com", "password": "wrong"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Invalid email or password.")

    def test_post_invalid_form_renders_page(self):
        resp = self.client.post(reverse("login"), {"email": "not-an-email", "password": "x"})
        self.assertEqual(resp.status_code, 200)


class RegisterViewTest(TestCase):
    def test_get_renders_form(self):
        resp = self.client.get(reverse("register"))
        self.assertEqual(resp.status_code, 200)

    def test_post_valid_creates_user_and_logs_in(self):
        resp = self.client.post(
            reverse("register"),
            {"email": "new@x.com", "username": "newbie", "password": "pw123456"},
        )
        self.assertRedirects(resp, reverse("home"))
        self.assertTrue(User.objects.filter(username="newbie").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_post_invalid_form_rerenders(self):
        resp = self.client.post(reverse("register"), {"email": "bad", "username": "", "password": ""})
        self.assertEqual(resp.status_code, 200)

    def test_post_duplicate_email_shows_error(self):
        make_user()
        resp = self.client.post(
            reverse("register"),
            {"email": "alice@example.com", "username": "alice2", "password": "pw123456"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This email has already been taken.")

    def test_post_duplicate_username_shows_error(self):
        make_user()
        resp = self.client.post(
            reverse("register"),
            {"email": "alice2@example.com", "username": "alice", "password": "pw123456"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This username has already been taken.")

    def test_post_integrity_error_unknown_field_generic(self):
        """Cover the 'else' branch when clean_integrity_error returns something unexpected."""
        with patch("accounts.views.clean_integrity_error", return_value="bogus_field"):
            with patch.object(User.objects, "create_user", side_effect=IntegrityError("boom")):
                resp = self.client.post(
                    reverse("register"),
                    {"email": "z@x.com", "username": "zzz", "password": "pw123456"},
                )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Registration failed.")


class SettingsViewTest(TestCase):
    def test_anonymous_redirects_to_login(self):
        resp = self.client.get(reverse("settings"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", cast(HttpResponseRedirect, resp).url)

    def test_get_authenticated_renders_form(self):
        user = make_user()
        self.client.force_login(user)
        resp = self.client.get(reverse("settings"))
        self.assertEqual(resp.status_code, 200)

    def test_post_updates_profile_without_password(self):
        user = make_user()
        self.client.force_login(user)
        resp = self.client.post(
            reverse("settings"),
            {
                "email": "alice@example.com",
                "username": "alice",
                "bio": "new bio",
                "image": "",
                "password": "",
            },
        )
        self.assertEqual(resp.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.bio, "new bio")
        self.assertTrue(user.check_password("pw123456"))

    def test_post_updates_profile_with_password(self):
        user = make_user()
        self.client.force_login(user)
        resp = self.client.post(
            reverse("settings"),
            {
                "email": "alice@example.com",
                "username": "alice",
                "bio": "",
                "image": "",
                "password": "newpw98765",
            },
        )
        self.assertEqual(resp.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.check_password("newpw98765"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_post_invalid_form_rerenders(self):
        user = make_user()
        self.client.force_login(user)
        resp = self.client.post(
            reverse("settings"),
            {"email": "bad", "username": "", "bio": "", "image": "", "password": ""},
        )
        self.assertEqual(resp.status_code, 200)


class LogoutViewTest(TestCase):
    def test_post_logs_out(self):
        user = make_user()
        self.client.force_login(user)
        resp = self.client.post(reverse("logout"))
        self.assertRedirects(resp, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_get_not_allowed(self):
        resp = self.client.get(reverse("logout"))
        self.assertEqual(resp.status_code, 405)


class ProfileViewTest(TestCase):
    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(email="bob@x.com", username="bob")
        self.article = Article.objects.create(author=self.alice, title="Alice Post", summary="s", content="c")

    def test_unknown_user_returns_404(self):
        resp = self.client.get(reverse("profile", args=["ghost"]))
        self.assertEqual(resp.status_code, 404)

    def test_profile_shows_authored_articles(self):
        resp = self.client.get(reverse("profile", args=["alice"]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Alice Post")

    def test_profile_favorites_tab(self):
        self.article.favorites.add(self.bob)
        resp = self.client.get(reverse("profile_favorites", args=["bob"]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Alice Post")

    def test_profile_pagination_valid_page(self):
        resp = self.client.get(reverse("profile", args=["alice"]) + "?page=1")
        self.assertEqual(resp.status_code, 200)

    def test_profile_pagination_invalid_page_defaults_to_one(self):
        resp = self.client.get(reverse("profile", args=["alice"]) + "?page=bogus")
        self.assertEqual(resp.status_code, 200)

    def test_profile_self_view_sets_is_self(self):
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("profile", args=["alice"]))
        self.assertTrue(resp.context["is_self"])
        self.assertFalse(resp.context["is_following"])

    def test_profile_authenticated_following_flag(self):
        self.alice.followers.add(self.bob)  # bob follows alice
        self.client.force_login(self.bob)
        resp = self.client.get(reverse("profile", args=["alice"]))
        self.assertTrue(resp.context["is_following"])


class FollowViewTest(TestCase):
    def setUp(self):
        self.alice = make_user()
        self.bob = make_user(email="bob@x.com", username="bob")

    def test_anonymous_redirects(self):
        resp = self.client.post(reverse("follow", args=["alice"]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", cast(HttpResponseRedirect, resp).url)

    def test_follow_then_unfollow(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("follow", args=["alice"]))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(self.alice.followers.filter(pk=self.bob.pk).exists())

        resp = self.client.post(reverse("follow", args=["alice"]))
        self.assertFalse(self.alice.followers.filter(pk=self.bob.pk).exists())

    def test_follow_self_is_noop(self):
        self.client.force_login(self.alice)
        resp = self.client.post(reverse("follow", args=["alice"]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(self.alice.followers.filter(pk=self.alice.pk).exists())

    def test_follow_htmx_returns_partial(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("follow", args=["alice"]), HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)

    def test_follow_unknown_user_404(self):
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("follow", args=["ghost"]))
        self.assertEqual(resp.status_code, 404)
