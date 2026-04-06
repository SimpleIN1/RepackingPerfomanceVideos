from django.urls import path

from AccountApp import views


urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("login/2fa/", views.Login2FAView.as_view(), name="login-2fa"),

    path("logout/", views.LogoutView.as_view(), name="logout"),

    path("register/", views.RegisterCreateView.as_view(), name="register"),
]
