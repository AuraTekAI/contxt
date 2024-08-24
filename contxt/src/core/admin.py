from core.models import *
from sms_app.models import SMS
from process_emails.models import Email

from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin

# Register models with the Django admin site.

# Registers the UserMessage model with the Django admin interface.
# This allows the UserMessage model to be managed through the Django admin interface.
admin.site.register(UserMessage)

# Registers the Log model with the Django admin interface.
# This allows the Log model to be managed through the Django admin interface.
admin.site.register(Log)

# Registers the SMS model with the Django admin interface.
# This allows the SMS model to be managed through the Django admin interface.
admin.site.register(SMS)

# Registers the Contact model with the Django admin interface.
# This allows the Contact model to be managed through the Django admin interface.
admin.site.register(Contact)

# Registers the Email model with the Django admin interface.
# This allows the Email model to be managed through the Django admin interface.
admin.site.register(Email)

# Registers the TransactionHistory model with the Django admin interface.
# This allows the TransactionHistory model to be managed through the Django admin interface.
admin.site.register(TransactionHistory)

# Unregisters the Group model from the Django admin interface.
# The Group model is removed from the admin interface as it is not required to be managed here.
admin.site.unregister(Group)
