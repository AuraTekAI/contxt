from core.models import *
from sms_app.models import SMS
from process_emails.models import Email

from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin


admin.site.register(UserMessage)
admin.site.register(Log)
admin.site.register(SMS)
admin.site.register(Contact)
admin.site.register(Email)
admin.site.register(TransactionHistory)
admin.site.unregister(Group)
