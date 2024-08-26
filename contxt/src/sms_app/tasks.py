
from contxt.celery import CustomExceptionHandler

from django.core.management import call_command
from django.conf import settings

from celery import shared_task


@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def schedule_send_sms(self):
    """
    Celery task for scheduling the sending SMS.

    This task is used to trigger the Django management command `send_sms`, which processes unread emails
    from the Corrlinks inbox. The task is executed only if the environment is not set to 'LOCAL'.

    Args:
        self (Task): The current task instance. Used for exception handling.

    Notes:
        - The task uses `CustomExceptionHandler` to handle any exceptions that occur during execution.
        - The task is bound to the 'scheduling_queue' queue.
    """
    if not settings.ENVIRONMENT == 'LOCAL':
        call_command('send_sms')
