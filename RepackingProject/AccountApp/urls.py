from django.urls import path

from AccountApp import views


urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("login/2fa/", views.Login2FAView.as_view(), name="login-2fa"),

    path("logout/", views.LogoutView.as_view(), name="logout"),

    path("register/", views.RegisterCreateView.as_view(), name="register"),

    path("forgotpassword/", views.ForgotPasswordView.as_view(), name="forgot-password"),
    path("forgotpassword/confirm/", views.ConfirmForgotPasswordView.as_view(), name="confirm-forgot-password"),
    path("forgotpassword/change/", views.ChangeForgotPasswordView.as_view(), name="change-forgot-password"),

    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/confirm-email/", views.ConfirmEmailView.as_view(), name="confirm-email-profile"),
    path("profile/info/", views.BaseInfoProfileView.as_view(), name="base-info-profile"),
    path("profile/changepassword/", views.ChangePasswordProfileView.as_view(), name="change-password-profile"),
    path("profile/security/", views.SecurityProfileView.as_view(), name="security-profile"),
]
