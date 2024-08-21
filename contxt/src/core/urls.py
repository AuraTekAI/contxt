from django.urls import path
from django.conf import settings

from core.views import cache_test, test_home


urlpatterns = [
    path('', test_home, name='test-home'), # TODO Move this to test urls
]
if settings.TEST_MODE == True:
    urlpatterns.append(path('cache/', cache_test, name='cache-test'),)
