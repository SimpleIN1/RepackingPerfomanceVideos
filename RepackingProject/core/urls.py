from django.urls import path

from core import views


urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("404", views.not_found_view, name="not-found"),
]
