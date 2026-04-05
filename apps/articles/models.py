from typing import Self

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from taggit.managers import TaggableManager


class ArticleQuerySet(models.QuerySet):
    def with_favorites(self, user: AbstractBaseUser | AnonymousUser) -> Self:
        return self.annotate(
            num_favorites=models.Count("favorites"),
            is_favorite=(
                models.Exists(get_user_model().objects.filter(pk=user.pk, favorites=models.OuterRef("pk")))
                if user.is_authenticated
                else models.Value(False, output_field=models.BooleanField())
            ),
        )

    def visible_to(self, user: AbstractBaseUser | AnonymousUser) -> Self:
        """Filter to articles the given user is allowed to see.

        Published articles are visible to everyone. Drafts are visible only
        to their author. Anonymous users see only published articles.
        """
        if user.is_authenticated:
            return self.filter(models.Q(is_published=True) | models.Q(author=user))
        return self.filter(is_published=True)


ArticleManager = models.Manager.from_queryset(ArticleQuerySet)


class Article(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=150, unique=True, blank=False)
    summary = models.TextField(blank=True)
    content = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True)

    is_published = models.BooleanField(default=True, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    tags = TaggableManager(blank=True)
    favorites = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="favorites")
    slug = models.SlugField(unique=True, max_length=255)  # Not a property as used for lookup

    objects = ArticleManager()

    def save(self, *args, **kwargs) -> None:
        if not self.pk:
            self.slug = slugify(self.title)
        if self.is_published and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
