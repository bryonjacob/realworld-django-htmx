from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from taggit.models import Tag

from articles.forms import ArticleForm
from articles.models import Article
from helpers.htmx import is_htmx
from helpers.pagination import paginate

User = get_user_model()

ARTICLES_PER_PAGE = 10


def _build_feed(request, tag=None):
    """Shared logic for home and tag views."""
    feed = request.GET.get("feed")

    queryset = Article.objects.with_favorites(request.user)

    if feed == "following" and not request.user.is_authenticated:
        return redirect("login")
    if feed == "following" and request.user.is_authenticated:
        followed_authors = User.objects.filter(followers=request.user)
        queryset = queryset.filter(author__in=followed_authors)
        active_tab = "following"
    elif tag:
        queryset = queryset.filter(tags__name=tag)
        active_tab = "tag"
    else:
        active_tab = "global"

    queryset = queryset.select_related("author").prefetch_related("tags").order_by("-created")
    page_result = paginate(queryset, request, per_page=ARTICLES_PER_PAGE)

    tags = cache.get_or_set("all_tags", Tag.objects.all, timeout=300)

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


def article_detail_view(request, slug):
    try:
        article = (
            Article.objects.with_favorites(request.user)
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
    cache.delete("all_tags")


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
    article = get_object_or_404(Article, slug=slug)
    if article.favorites.filter(id=request.user.id).exists():
        article.favorites.remove(request.user)
    else:
        article.favorites.add(request.user)
    article = Article.objects.with_favorites(request.user).select_related("author").get(pk=article.pk)
    if is_htmx(request):
        return render(request, "partials/favorite_button.html", {"article": article})
    return redirect("article_detail", slug=slug)
