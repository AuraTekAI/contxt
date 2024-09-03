from django.contrib import admin
from sms_app.models import SMS

class SMSAdmin(admin.ModelAdmin):
    # Fields to be displayed in the list view
    list_display = (
        'text_id',
        'bot',
        'contact',
        'email',
        'phone_number',
        'direction',
        'status',
        'is_processed',
        'created_at',
        'updated_at',
    )

    # Fields that are clickable to edit the instance
    list_display_links = ('text_id', 'contact', 'email')

    # Fields to be used for filtering in the list view
    list_filter = (
        'direction',
        'bot',
        'status',
        'is_processed',
        'created_at',
        'updated_at',
    )

    # Fields to be used for searching in the list view
    search_fields = ('text_id', 'phone_number', 'message', 'contact__name', 'email__address')

    # Fields to be displayed in the detail view and edit form
    fields = (
        'text_id',
        'contact',
        'bot',
        'email',
        'message',
        'phone_number',
        'direction',
        'status',
        'is_processed',
        'created_at',
        'updated_at',
    )

    # Make fields read-only if they should not be editable
    readonly_fields = ('created_at', 'updated_at')

    # Customize how the model is ordered in the list view
    ordering = ('-created_at',)

    # Define which fields are shown in the list view, detail view, and filterable
    def get_list_display(self, request):
        if request.user.is_superuser:
            return super().get_list_display(request)
        return ('text_id', 'contact', 'bot', 'email', 'phone_number', 'direction', 'status', 'is_processed', 'created_at')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('text_id',)
        return self.readonly_fields

admin.site.register(SMS, SMSAdmin)
