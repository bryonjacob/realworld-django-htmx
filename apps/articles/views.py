from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from taggit.models import Tag

from articles.constants import (
    ALL_TAGS_CACHE_KEY,
    ALL_TAGS_CACHE_TTL_SECONDS,
    ARTICLES_PER_PAGE,
)
from articles.forms import ArticleForm
from articles.models import Article
from helpers.htmx import is_htmx
from helpers.pagination import paginate

User = get_user_model()


def _feed_queryset(
    user: AbstractBaseUser | AnonymousUser,
    feed: str | None,
    tag: str | None,
) -> tuple[QuerySet | None, str]:
    """Build article queryset for the requested feed.

    Returns (queryset, active_tab). queryset is None when an anonymous user
    requested the 'following' feed — the caller should redirect to login.

    Feeds never include drafts — even the author's own. Drafts live only
    on the drafts tab of the author's profile.
    """
    queryset = Article.objects.with_favorites(user).filter(is_published=True)
    if feed == "following":
        if not user.is_authenticated:
            return None, "following"
        followed_authors = User.objects.filter(followers=user)
        return queryset.filter(author__in=followed_authors), "following"
    if tag:
        return queryset.filter(tags__name=tag), "tag"
    return queryset, "global"


def _build_feed(request, tag=None):
    """Shared logic for home and tag views."""
    feed = request.GET.get("feed")
    queryset, active_tab = _feed_queryset(request.user, feed, tag)
    if queryset is None:
        return redirect("login")

    queryset = queryset.select_related("author").prefetch_related("tags").order_by("-published_at")
    page_result = paginate(queryset, request, per_page=ARTICLES_PER_PAGE)

    def _published_tags():
        return list(Tag.objects.filter(article__is_published=True).distinct())

    tags = cache.get_or_set(ALL_TAGS_CACHE_KEY, _published_tags, timeout=ALL_TAGS_CACHE_TTL_SECONDS)

    context = {
        "articles": page_result.items,
        "tags": tags,
        "active_tab": active_tab,
        "active_tag": tag,
        "page": page_result.page,
        "pages": page_result.pages,
    }

    if is_htmx(request):
        return render(request, "partials/feed_content.html", context)
    return render(request, "articles/home.html", context)


def home_view(request):
    tag = request.GET.get("tag")
    return _build_feed(request, tag=tag)


def tag_view(request, tag):
    return _build_feed(request, tag=tag)


def profile_view(request, username, tab):
    """Render a user profile page with their articles or favorited articles.

    Lives in articles (not accounts) because the body is article-listing
    logic. The URL still belongs to the accounts app — see accounts/urls.py
    and the thin shims in accounts/views.py.
    """
    try:
        profile_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return render(request, "accounts/profile_404.html", {"username": username}, status=404)

    is_self = request.user == profile_user
    is_following = request.user.is_authenticated and request.user.is_following(profile_user)
    queryset = (
        Article.objects.with_favorites(request.user)
        .filter(is_published=True)
        .select_related("author")
        .prefetch_related("tags")
    )
    if tab == "favorites":
        queryset = queryset.filter(favorites=profile_user)
    else:
        queryset = queryset.filter(author=profile_user)
    queryset = queryset.order_by("-published_at")
    page_result = paginate(queryset, request, per_page=ARTICLES_PER_PAGE)

    return render(
        request,
        "accounts/profile.html",
        {
            "profile_user": profile_user,
            "is_self": is_self,
            "is_following": is_following,
            "articles": page_result.items,
            "tab": tab,
            "page": page_result.page,
            "pages": page_result.pages,
        },
    )


def article_detail_view(request, slug):
    try:
        article = (
            Article.objects.with_favorites(request.user)
            .visible_to(request.user)
            .select_related("author")
            .prefetch_related("tags")
            .get(slug=slug)
        )
    except Article.DoesNotExist:
        return render(request, "articles/detail_404.html", {"slug": slug}, status=404)
    comments = article.comment_set.select_related("author").order_by("-created")
    is_following = request.user.is_authenticated and request.user.is_following(article.author)
    return render(
        request,
        "articles/detail.html",
        {
            "article": article,
            "comments": comments,
            "is_following": is_following,
        },
    )


def _save_article_form(form, article):
    """Map form fields (description/body) to model fields (summary/content) and save."""
    article.title = form.cleaned_data["title"]
    article.summary = form.cleaned_data.get("description", "")
    article.content = form.cleaned_data.get("body", "")
    article.save()
    tag_string = form.cleaned_data.get("tags", "")
    article.tags.clear()
    if tag_string:
        for tag_name in tag_string.split(","):
            tag_name = tag_name.strip()
            if tag_name:
                article.tags.add(tag_name)
    cache.delete(ALL_TAGS_CACHE_KEY)


@login_required
def article_create_view(request):
    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = Article(author=request.user)
            _save_article_form(form, article)
            return redirect("article_detail", slug=article.slug)
    else:
        form = ArticleForm()
    return render(request, "articles/editor.html", {"form": form})


@login_required
def article_edit_view(request, slug):
    article = get_object_or_404(Article, slug=slug, author=request.user)
    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            _save_article_form(form, article)
            return redirect("article_detail", slug=article.slug)
    else:
        form = ArticleForm(
            initial={
                "title": article.title,
                "description": article.summary,
                "body": article.content,
                "tags": ", ".join(t.name for t in article.tags.all()),
            }
        )
    return render(request, "articles/editor.html", {"form": form, "article": article})


@login_required
@require_POST
def article_delete_view(request, slug):
    article = get_object_or_404(Article, slug=slug, author=request.user)
    article.delete()
    return redirect("home")


@login_required
@require_POST
def article_favorite_view(request, slug):
    article = get_object_or_404(Article.objects.visible_to(request.user), slug=slug, is_published=True)
    if article.favorites.filter(id=request.user.id).exists():
        article.favorites.remove(request.user)
    else:
        article.favorites.add(request.user)
    article = Article.objects.with_favorites(request.user).select_related("author").get(pk=article.pk)
    if is_htmx(request):
        return render(request, "partials/favorite_button.html", {"article": article})
    return redirect("article_detail", slug=slug)
