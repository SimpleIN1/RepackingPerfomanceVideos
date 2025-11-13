import json
import logging
from http import HTTPStatus

from django.views import View
from django.conf import settings
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.forms.models import model_to_dict
from django.shortcuts import render, redirect
from django.contrib.sessions.models import Session
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib.sessions.backends.db import SessionStore
from django.views.generic.edit import CreateView, UpdateView
from silk.profiling.profiler import silk_profile

from AccountApp import forms
from AccountApp.services.user import get_user, change_password_by_user_id_from_session
from AccountApp.models import UserModel
from common.code_generator import generate_code
from common.mail.email_user import ConfirmationEmailUser
from common.mail.mail import Confirmation2FAEmail, ConfirmationForgotPasswordEmail, ConfirmationEmail
from AccountApp.services.confirm_email_user import send_confirmation_email
from AccountApp.services.session_service import ConfirmationCodeSessionService, UserSession


class LoginView(View):
    template_name = "account/login.html"
    form_class = forms.LoginForm

    # @method_decorator(cache_page(60 * 60 * 12), name='dispatch')
    def get(self, request):
        context = {"form": self.form_class()}

        request.session["init"] = "init"

        if request.user.is_authenticated:
            return redirect("repacking-records")

        return render(request, self.template_name, context=context)

    @method_decorator(csrf_protect)
    def post(self, request):
        context = {}
        form = self.form_class(request.POST)

        if not form.is_valid():
            context["form"] = form
            return render(request, self.template_name, context=context)

        user = authenticate(request, **form.cleaned_data)

        if not user:
            context["form"] = form
            form.add_error(None, "Некорректный email или пароль")
            return render(request, self.template_name, context=context)

        # redirect 2FA
        if user.two_factor_auth:
            cm_user = ConfirmationEmailUser(
                user, request.session, settings.KIND_CODE_2FA,
                "login-2fa", Confirmation2FAEmail
            )
            send_confirmation_email(cm_user)
            return redirect("login-2fa")

        login(request, user)

        return redirect("repacking-records")


class Login2FAView(View):
    template_name = "account/login-2fa.html"
    form_class = forms.Login2FAForm

    def get(self, request):
        context = {"form": self.form_class()}

        session_id = request.GET.get("session_id")
        if session_id:
            try:
                session_id_db = Session.objects.get(pk=session_id)
                if session_id_db:
                    request.session.session_key = session_id
            except Session.DoesNotExist:
                return redirect("not_found")

        if request.user.is_authenticated:
            return redirect("repacking-records")

        return render(request, self.template_name, context=context)

    @method_decorator(csrf_protect)
    def post(self, request):

        if request.user.is_authenticated:
            return redirect("repacking-records")

        context = {}
        form = self.form_class(request.POST)

        form.session = request.session

        if not form.is_valid():
            context["form"] = form
            return render(request, self.template_name, context=context)

        user_id = form.get_user_id()
        if not user_id:
            dict_message = {
                "title": "Аутентификация 2FA",
                "message": "Ошибка аутентификации 2FA. Перезагрузите страницу или выполните повторный вход."
            }
            messages.error(request, json.dumps(dict_message), extra_tags="json_data")
            return redirect("login")

        user = get_user(id=user_id)

        if not user:
            return redirect("login")

        login(request, user)

        return redirect("repacking-records")


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        ccm = ConfirmationCodeSessionService(request.session, request.user)
        ccm.clear()
        logout(request)
        return redirect("login")


class RegisterCreateView(CreateView):
    model = UserModel
    form_class = forms.RegisterModelForm
    template_name = "account/register.html"
    success_url = reverse_lazy('login')

    def get(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            return redirect("repacking-records")

        return super().get(request, *args, **kwargs)

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if self.object:
            dict_message = {
                "title": "Регистрация",
                "message": "Пользователь создан успешно. Дождитесь пока выдадут доступ."
            }
            messages.success(request, json.dumps(dict_message), extra_tags="json_data")

        return response


class ForgotPasswordView(View):
    template_name = "account/forgot-password.html"
    form_class = forms.ForgotPasswordForm

    def get(self, request):
        context = {"form": self.form_class()}

        if request.user.is_authenticated:
            return redirect("repacking-records")

        return render(request, self.template_name, context=context)

    @method_decorator(csrf_protect)
    def post(self, request):

        if request.user.is_authenticated:
            return redirect("repacking-records")

        context = {}
        form = self.form_class(request.POST)
        form.session = request.session

        if not form.is_valid():
            context["form"] = form
            return render(request, self.template_name, context=context)

        cm_user = ConfirmationEmailUser(
            form.user, request.session, settings.KIND_CODE_FORGOT_PASSWORD,
            "confirm-forgot-password", ConfirmationForgotPasswordEmail
        )
        send_confirmation_email(cm_user)

        return redirect("confirm-forgot-password")


class ConfirmForgotPasswordView(View):
    template_name = "account/confirm-forgot-password.html"
    form_class = forms.ConfirmForgotPasswordForm
    user_auth_redirect_route = "repacking-records"

    def get(self, request):
        context = {"form": self.form_class()}

        if request.user.is_authenticated:
            return redirect(self.user_auth_redirect_route)

        return render(request, self.template_name, context=context)

    @method_decorator(csrf_protect)
    def post(self, request):

        if request.user.is_authenticated:
            return redirect(self.user_auth_redirect_route)

        context = {}
        form = self.form_class(request.POST)
        form.session = request.session

        if not form.is_valid():
            context["form"] = form
            return render(request, self.template_name, context=context)

        # if not form.check_code(request.session):
        #     context["form"] = form
        #     return render(request, self.template_name, context=context)

        return redirect("change-forgot-password")


class ChangeForgotPasswordView(View):
    template_name = "account/change-forgot-password.html"
    form_class = forms.ChangePasswordForgotPasswordForm

    def get(self, request):
        context = {"form": self.form_class()}

        if request.user.is_authenticated:
            return redirect("repacking-records")

        return render(request, self.template_name, context=context)

    @method_decorator(csrf_protect)
    def post(self, request):
        context = {}
        form = self.form_class(request.POST)

        if not form.is_valid():
            context["form"] = form
            return render(request, self.template_name, context=context)

        if not change_password_by_user_id_from_session(
                form.cleaned_data["password"], request.session
        ):
            form.add_error(None, "При изменение пароля произошла ошибка")
            return render(request, self.template_name, context=context)

        dict_message = {
            "title": "Изменение пароля",
            "message": "Пароль успешно изменен."
        }
        messages.success(request, json.dumps(dict_message), extra_tags="json_data")
        return redirect("login")


class ProfileView(LoginRequiredMixin, View):
    template_name = "account/profile.html"

    def get(self, request):
        user_info = model_to_dict(request.user, fields=forms.BaseInfoProfileGETForm.fields)
        user_security = model_to_dict(request.user, fields=forms.SecurityProfileForm.fields)
        form_info = forms.BaseInfoProfileGETForm(user_info)
        form_security = forms.SecurityProfileForm(user_security)

        context = {
            "baseInfoProfileForm": form_info,
            "changePasswordProfileForm": forms.ChangePasswordProfileForm(),
            "security2FAProfileForm": form_security,
        }

        return render(request, self.template_name, context=context)


class BaseInfoProfileView(LoginRequiredMixin, View):
    form_class = forms.BaseInfoProfilePOSTForm

    @method_decorator(csrf_protect)
    def post(self, request):
        context = {}

        form = self.form_class(request.POST)
        form.set_current_user(request.user)

        if not form.is_valid():
            context["form"] = form
            return HttpResponse(
                json.dumps({
                    "success": False,
                    "fields": dict(form.errors)
                }),
                content_type='application/json',
                status=HTTPStatus.BAD_REQUEST
            )

        form.save(request.user)

        if request.user.email != form.cleaned_data["email"]:
            cm_user = ConfirmationEmailUser(
                request.user, request.session, settings.KIND_CODE_2FA,
                "confirm-email-profile", ConfirmationEmail,
                email=request.user.email
            )
            send_confirmation_email(cm_user)

            return HttpResponse(
                json.dumps({
                    "success": True,
                    "redirect": str(reverse_lazy("confirm-email-profile")),
                }),
                content_type='application/json',
                status=HTTPStatus.OK
            )

        return HttpResponse(
            json.dumps({"success": True}),
            content_type='application/json',
            status=HTTPStatus.OK
        )


class ConfirmEmailView(LoginRequiredMixin, View):
    template_name = "account/confirm-email.html"
    form_class = forms.ConfirmEmailForm

    def get(self, request):
        context = {"form": self.form_class()}
        return render(request, self.template_name, context=context)

    @method_decorator(csrf_protect)
    def post(self, request):

        context = {}
        form = self.form_class(request.POST)
        form.session = request.session

        if not form.is_valid():
            context["form"] = form
            return render(request, self.template_name, context=context)

        us = UserSession(request.user, request.session)
        form.save(us)

        dict_message = {
            "title": "Подтверждение email",
            "message": "Почтовый адрес успешно изменен и подтевержден."
        }
        messages.success(request, json.dumps(dict_message), extra_tags="json_data")
        return redirect("profile")


class ChangePasswordProfileView(LoginRequiredMixin, View):
    form_class = forms.ChangePasswordProfileForm

    @method_decorator(csrf_protect)
    def post(self, request):
        context = {}

        form = self.form_class(request.POST)
        form.set_user(request.user)

        if not form.is_valid():
            context["form"] = form
            return HttpResponse(
                json.dumps({
                    "success": False,
                    "fields": dict(form.errors)
                }),
                content_type='application/json',
                status=HTTPStatus.BAD_REQUEST
            )

        form.save(request.user)

        return HttpResponse(
            json.dumps({"success": True}),
            content_type='application/json',
            status=HTTPStatus.OK
        )


class SecurityProfileView(LoginRequiredMixin, View):
    form_class = forms.SecurityProfileForm

    @method_decorator(csrf_protect)
    def post(self, request):
        context = {}
        form = self.form_class(request.POST)

        if not form.is_valid():
            context["form"] = form
            return HttpResponse(
                json.dumps({
                    "success": False,
                    "fields": dict(form.errors)
                }),
                content_type='application/json',
                status=HTTPStatus.BAD_REQUEST
            )

        form.save(request.user)

        return HttpResponse(
            json.dumps({
                "success": True,
            }),
            content_type='application/json',
            status=HTTPStatus.OK
        )
