from django.urls import path

from accounts import views

urlpatterns = [
    path("login", views.login_view, name="login"),
    path("register", views.register_view, name="register"),
    path("settings", views.settings_view, name="settings"),
    path("logout", views.logout_view, name="logout"),
    path("profile/<str:username>", views.profile_view, name="profile"),
    path("profile/<str:username>/favorites", views.profile_favorites_view, name="profile_favorites"),
    path("profile/<str:username>/drafts", views.profile_drafts_view, name="profile_drafts"),
    path("profile/<str:username>/follow", views.follow_view, name="follow"),
]
