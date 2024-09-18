
from contxt.celery import CustomExceptionHandler

from django.core.management import call_command
from django.conf import settings

from celery import shared_task

@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def push_new_email_task(self, pic_name=None, message_content=None, bot_id=None, is_accept_invite=None):
    """
    Celery task to run the push_new_emails management command.

    Args:
        pic_name (str): The name to be processed (optional).
        message_content (str): The content of the email message (optional).
        bot_id (int): The bot ID executing the task (optional).
        is_accept_invite (bool): Whether the bot accepts an invite (optional).

    Returns:
        str: The output or status of the command.
    """
    try:
        call_command(
            'push_new_emails',
            pic_name=pic_name,
            message_content=message_content,
            bot_id=bot_id,
            is_accept_invite=is_accept_invite
        )
    except Exception as e:
        print(f'Error occurred = {e}')

