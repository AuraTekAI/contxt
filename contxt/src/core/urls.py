from django.urls import path
from django.conf import settings

from core.views import cache_test


urlpatterns = []
if settings.ENVIRONMENT == 'LOCAL':
    urlpatterns.append(path('cache/', cache_test, name='cache-test'),)
