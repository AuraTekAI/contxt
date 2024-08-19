from django.urls import path
from django.conf import settings

from core.views import cache_test, test_home


urlpatterns = [
    path('', test_home, name='test-home'),
]
if settings.ENVIRONMENT == 'LOCAL':
    urlpatterns.append(path('cache/', cache_test, name='cache-test'),)
