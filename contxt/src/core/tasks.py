
from contxt.celery import CustomExceptionHandler

from django.core.management import call_command

from celery import shared_task


@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def schedule_test_command(self):
    call_command('test_scheduling')
