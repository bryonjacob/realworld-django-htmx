from django.urls import path

from articles import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("tag/<str:tag>", views.tag_view, name="tag"),
    path("editor", views.article_create_view, name="article_create"),
    path("editor/<slug:slug>", views.article_edit_view, name="article_edit"),
    path("article/<slug:slug>", views.article_detail_view, name="article_detail"),
    path("article/<slug:slug>/delete", views.article_delete_view, name="article_delete"),
    path("article/<slug:slug>/favorite", views.article_favorite_view, name="article_favorite"),
    path("article/<slug:slug>/publish", views.article_publish_view, name="article_publish"),
]
