from core.models import *

from django.contrib import admin
from django.contrib.auth.models import Group

from django.contrib import admin
from .models import Contact

class ContactAdmin(admin.ModelAdmin):
    """
    Admin interface for managing Contact records.

    Provides functionality to view, edit, and manage Contact records.
    """

    # Fields to display in the list view
    list_display = (
        'contact_name',
        'phone_number',
        'email',
        'user',
        'created_at',
        'updated_at',
    )

    # Fields that are clickable to edit the instance
    list_display_links = ('contact_name', 'phone_number')

    # Fields to be used for filtering in the list view
    list_filter = (
        'user',
        'created_at',
        'updated_at',
    )

    # Fields to be used for searching in the list view
    search_fields = ('contact_name', 'phone_number', 'email', 'user__username')

    # Fields to be displayed in the detail view and edit form
    fields = (
        'user',
        'contact_name',
        'phone_number',
        'email',
        'created_at',
        'updated_at',
    )

    # Make fields read-only if they should not be editable
    readonly_fields = ('created_at', 'updated_at')

    # Customize how the model is ordered in the list view
    ordering = ('-created_at',)

    def get_list_display(self, request):
        """
        Customize the list display based on user permissions or other logic.

        Args:
            request (HttpRequest): The request object.

        Returns:
            tuple: The tuple of fields to display in the list view.
        """
        if request.user.is_superuser:
            return super().get_list_display(request)
        return ('contact_name', 'phone_number', 'email', 'user')

    def get_readonly_fields(self, request, obj=None):
        """
        Determine which fields should be read-only based on user permissions or other logic.

        Args:
            request (HttpRequest): The request object.
            obj (Contact, optional): The current instance of the model being edited.

        Returns:
            tuple: The tuple of read-only fields.
        """
        if obj:  # Editing an existing object
            return self.readonly_fields + ('user',)
        return self.readonly_fields

class ContactManagementResponseMessagesAdmin(admin.ModelAdmin):
    list_display = ('message_key', 'response_content', 'created_at', 'updated_at')
    list_filter = ('created_at', 'message_key')
    search_fields = ('message_key', 'response_content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def get_readonly_fields(self, request, obj=None):
        # Optionally make fields readonly based on user or other conditions
        if request.user.is_superuser:
            return self.readonly_fields
        return ('created_at', 'updated_at')


# Registers the Contact model with the Django admin interface.
# This allows the Contact model to be managed through the Django admin interface.
admin.site.register(Contact, ContactAdmin)

# Registers the Contact model with the Django admin interface.
# This allows the Contact model to be managed through the Django admin interface.
admin.site.register(ContactManagementResponseMessages, ContactManagementResponseMessagesAdmin)

# Unregisters the Group model from the Django admin interface.
# The Group model is removed from the admin interface as it is not required to be managed here.
admin.site.unregister(Group)
