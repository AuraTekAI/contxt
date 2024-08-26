
from sms_app.views import textbelt_webhook,sms_api_test

from django.urls import path
from django.conf import settings

urlpatterns = [
    path('sms/', textbelt_webhook, name='textbelt-webhook',)
]
if settings.TEST_MODE == True:
    urlpatterns.append(path('sms/test/', sms_api_test, name='sms-api-test'),)
