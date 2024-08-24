
from contxt.celery import CustomExceptionHandler

from django.core.management import call_command
from django.conf import settings

from celery import shared_task


@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def schedule_pull_email(self):
    """
    Celery task for scheduling the pulling of emails.

    This task is used to trigger the Django management command `pull_emails`, which processes unread emails
    from the Corrlinks inbox. The task is executed only if the environment is not set to 'LOCAL'.

    Args:
        self (Task): The current task instance. Used for exception handling.

    Notes:
        - The task uses `CustomExceptionHandler` to handle any exceptions that occur during execution.
        - The task is bound to the 'scheduling_queue' queue.
    """
    if not settings.ENVIRONMENT == 'LOCAL':
        call_command('pull_emails')


@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def schedule_push_email(self):
    """
    Celery task for scheduling the pushing of email replies.

    This task is used to trigger the Django management command `push_emails`, which sends email replies
    as part of the push email process. The task is executed only if the environment is not set to 'LOCAL'.

    Args:
        self (Task): The current task instance. Used for exception handling.

    Notes:
        - The task uses `CustomExceptionHandler` to handle any exceptions that occur during execution.
        - The task is bound to the 'scheduling_queue' queue.
    """
    if not settings.ENVIRONMENT == 'LOCAL':
        call_command('push_emails')
