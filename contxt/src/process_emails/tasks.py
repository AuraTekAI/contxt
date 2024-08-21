
from contxt.celery import CustomExceptionHandler

from django.core.management import call_command
from django.conf import settings

from celery import shared_task


@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def schedule_pull_email(self):
    if not settings.ENVIRONMENT == 'LOCAL':
        call_command('pull_emails')

@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def schedule_push_email(self):
    if not settings.ENVIRONMENT == 'LOCAL':
        call_command('push_emails')
