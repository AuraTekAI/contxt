from contxt.celery import CustomExceptionHandler

from django.core.management import call_command
from django.conf import settings

from celery import shared_task

@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def schedule_accept_invites(self):
    """
    Celery task to run the Django management command for accepting invites.

    This task is designed to be run periodically to process and accept invites.
    It is executed by Celery and will only run if the environment is not set to 'LOCAL'.

    Args:
        self (celery.Task): The Celery task instance, used to access the task's context and configuration.

    Returns:
        None

    Notes:
        - Uses `call_command` to invoke the `accept_invites` management command.
        - Task execution is conditional on the environment variable `ENVIRONMENT` not being 'LOCAL'.
        - This task is scheduled to run on the 'scheduling_queue'.
        - The task inherits from `CustomExceptionHandler` to handle exceptions in a customized manner.
    """
    if not settings.ENVIRONMENT == 'LOCAL':
        call_command('accept_invites')
