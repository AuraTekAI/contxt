
from contxt.celery import CustomExceptionHandler

from django.core.management import call_command
from django.conf import settings

from celery import shared_task

import logging


logger = logging.getLogger('celery')
accept_invite_logger = logging.getLogger('accpet_invite')
push_email_logger = logging.getLogger('push_email')
pull_email_logger = logging.getLogger('pull_email')
send_sms_logger = logging.getLogger('send_sms')

@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def schedule_test_command(self):
    if settings.TEST_MODE == True:
        call_command('test_scheduling')
    else:
        pass

@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def entrypoint_for_bots(self, bot_id):

    accept_invite_logger.debug(f'Starting invites processing ......')
    accept_invite_logger.debug(f'Current bot id is {bot_id}')
    call_command('accept_invites', bot_id=bot_id)

    logger.debug(f'Starting pull emails processing ......')
    pull_email_logger.debug(f'Current bot id is {bot_id}')
    call_command('pull_emails', bot_id=bot_id)

    push_email_logger.debug(f'Starting push emails processing ......')
    push_email_logger.debug(f'Current bot id is {bot_id}')
    call_command('push_emails', bot_id=bot_id)

    send_sms_logger.debug(f'Starting send sms processing ......')
    send_sms_logger.debug(f'Current bot id is {bot_id}')
    call_command('send_sms', bot_id=bot_id)


@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def sync_bot_tasks_with_bots(self):
    call_command('sync_bots_with_bot_tasks')
