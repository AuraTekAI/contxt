
from contxt.celery import CustomExceptionHandler
from sms_app.utils import send_quota_limit_reached_notification

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

@shared_task(base=CustomExceptionHandler, bind=True, queue='generic_email_queue')
def send_quota_limit_reached_email_task(self, quota_limit=0):
    """
    Celery task to send an email notification when a reached quota limit.

    This task sends an email using the `send_quota_limit_reached_notification` function.
    The task is executed only if the environment is not set to 'LOCAL' and emails are enabled.

    Args:
        self (Task): The current task instance. Used for exception handling.
        quota_limit (int): The quota limit that has been reached.

    Notes:
        - The task uses `CustomExceptionHandler` to handle any exceptions that occur during execution.
        - The task is bound to the 'generic_email_queue' queue.
    """
    if not settings.ENVIRONMENT == 'LOCAL' and settings.EMAILS_ENABLED:
        try:
            send_quota_limit_reached_notification(quota_limit)
        except Exception as e:
            self.retry(exc=e, countdown=60, max_retries=3)
    else:
        print('SMS sending quota limit has been reached.')
