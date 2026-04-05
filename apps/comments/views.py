from articles.models import Article
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from comments.models import Comment
from helpers.htmx import is_htmx


@login_required
@require_POST
def comment_create_view(request, slug):
    article = get_object_or_404(Article, slug=slug)
    body = request.POST.get("body", "").strip()
    if body:
        Comment.objects.create(article=article, author=request.user, content=body)
    if is_htmx(request):
        comments = Comment.objects.filter(article=article).select_related("author").order_by("-created")
        return render(request, "partials/comment_list.html", {"comments": comments, "article": article})
    return redirect("article_detail", slug=slug)


@login_required
@require_POST
def comment_delete_view(request, slug, comment_id):
    article = get_object_or_404(Article, slug=slug)
    comment = get_object_or_404(Comment, id=comment_id, article=article)
    if comment.author != request.user and article.author != request.user:
        return HttpResponseForbidden()
    comment.delete()
    if is_htmx(request):
        comments = Comment.objects.filter(article=article).select_related("author").order_by("-created")
        return render(request, "partials/comment_list.html", {"comments": comments, "article": article})
    return redirect("article_detail", slug=slug)
