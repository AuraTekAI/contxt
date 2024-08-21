
from contxt.celery import CustomExceptionHandler

from django.core.management import call_command
from django.conf import settings

from celery import shared_task


@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def schedule_test_command(self):
    if settings.TEST_MODE == True:
        call_command('test_scheduling')
    else:
        pass
