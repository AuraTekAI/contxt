from django.urls import path
from django.conf import settings

from core.views import cache_test, test_home


urlpatterns = [

]
if settings.TEST_MODE == True:
    urlpatterns.append(path('cache/', cache_test, name='cache-test'),)
    urlpatterns.append(path('', test_home, name='test-home'),)
