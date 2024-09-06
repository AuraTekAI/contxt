
from core.models import User, BotAccount

from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin

class AccountAdmin(UserAdmin):
    """
    Customizes the Django admin interface for the User model by extending the built-in `UserAdmin` class.

    This class is used to manage how user accounts are displayed and handled in the Django admin panel.

    Attributes:
    - `ordering (tuple)`: Defines the default ordering of user accounts by `user_name`.
    - `list_display (tuple)`: Specifies the fields to be displayed in the list view of the admin panel.
      This includes fields like `user_name`, `name`, `age`, `sex`, `account_balance`, and various timestamps.
    - `search_fields (tuple)`: Allows the admin to search users by `user_name` and `name`.
    - `readonly_fields (tuple)`: Makes certain fields, such as `created_at` and `updated_at`, read-only to prevent modification in the admin panel.
    - `filter_horizontal (tuple)`: Used for horizontal filter widgets for many-to-many relationships; set as an empty tuple since it is not utilized.
    - `list_filter (tuple)`: Adds filters to the admin list view, allowing users to filter by `is_active`, `is_superuser`, and `sex`.
    - `fieldsets (tuple)`: Organizes the fields on the user detail page into logical groups:
        - Basic info like `user_name` and `password`.
        - Personal information such as `name`, `age`, `sex`, and `account_balance`.
        - Permissions, including fields like `is_active`, `is_staff`, `is_superuser`, `private_mode`, and related permissions and groups.
        - Important dates, including `last_login`, `created_at`, and `updated_at`.
    - `add_fieldsets (tuple)`: Defines the fields displayed when adding a new user through the admin interface. This differs slightly from `fieldsets` to streamline user creation.
      - Includes `user_name`, `name`, `password1`, `password2`, and personal information.
      - Permissions are also grouped here for initial account setup.

    Admin Integration:
    - The `AccountAdmin` class is registered with Django's admin site using `admin.site.register(User, AccountAdmin)`, which associates this customized admin interface with the `User` model.
    """

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

class BotAccountAdmin(admin.ModelAdmin):
    """
    Admin interface for managing BotAccount records.

    Provides functionality to view, edit, and manage BotAccount records.
    """

    list_display = (
        'bot_name',
        'email_address',
        'last_read_message_id',
        'is_active',
        'created_at',
        'updated_at',
    )

# Register the customized admin class with the User model
admin.site.register(User, AccountAdmin)
admin.site.register(BotAccount, BotAccountAdmin)
