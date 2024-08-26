
from process_emails.models import Email

from django.contrib import admin

class EmailAdmin(admin.ModelAdmin):
    """
    Admin interface for managing Email messages.

    Provides functionality to view, edit, and manage Email records.
    """

    # Fields to display in the list view
    list_display = (
        'message_id',
        'user',
        'subject',
        'sent_date_time',
        'is_processed',
        'created_at',
        'updated_at',
    )

    # Fields that are clickable to edit the instance
    list_display_links = ('message_id', 'subject', 'user')

    # Fields to be used for filtering in the list view
    list_filter = (
        'is_processed',
        'sent_date_time',
        'user',
    )

    # Fields to be used for searching in the list view
    search_fields = ('message_id', 'subject', 'body', 'user__username')

    # Fields to be displayed in the detail view and edit form
    fields = (
        'user',
        'message_id',
        'sent_date_time',
        'subject',
        'body',
        'is_processed',
        'created_at',
        'updated_at',
    )

    # Make fields read-only if they should not be editable
    readonly_fields = ('created_at', 'updated_at')

    # Customize how the model is ordered in the list view
    ordering = ('-sent_date_time',)

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
        return ('message_id', 'user', 'subject', 'sent_date_time', 'is_processed')

    def get_readonly_fields(self, request, obj=None):
        """
        Determine which fields should be read-only based on user permissions or other logic.

        Args:
            request (HttpRequest): The request object.
            obj (Email, optional): The current instance of the model being edited.

        Returns:
            tuple: The tuple of read-only fields.
        """
        if obj:  # Editing an existing object
            return self.readonly_fields + ('message_id',)
        return self.readonly_fields

admin.site.register(Email, EmailAdmin)
