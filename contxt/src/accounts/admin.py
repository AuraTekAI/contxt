from core.models import User

from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin

class AccountAdmin(UserAdmin):
    ordering = ("user_name",)
    list_display = (
        "user_name",
        "name",
        "age",
        "sex",
        "account_balance",
        "created_at",
        "updated_at",
        "is_superuser",
    )
    search_fields = ("user_name", "name")
    readonly_fields = ("created_at", "updated_at")

    filter_horizontal = ()
    list_filter = ("is_active", "is_superuser", "sex")
    fieldsets = (
        (None, {"fields": ("user_name", "password")}),
        ("Personal Info", {"fields": ("name", "age", "sex", "account_balance")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "private_mode",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("user_name", "name", "password1", "password2")}),
        ("Personal Info", {"fields": ("age", "sex", "account_balance")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )


admin.site.register(User, AccountAdmin)