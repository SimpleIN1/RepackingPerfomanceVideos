from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from AccountApp.models import UserModel


@admin.register(UserModel)
class UserModelAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"),
         {
             "fields": (
                 "last_name",
                 "first_name",
                 "middle_name",
                 "email",
             )
         }
         ),
        (_("Security"),
         {
             "fields": (
                 "two_factor_auth",
             ),
         }
         ),
        (_("Permissions"),
         {
             "fields": (
                 "is_active",
                 "is_staff",
                 "is_superuser",
                 "groups",
                 "user_permissions",
             ),
         },
         ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("id", "last_name", "first_name", "middle_name", "email", "is_active", "is_staff",)
