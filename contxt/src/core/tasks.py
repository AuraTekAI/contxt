
from contxt.celery import CustomExceptionHandler

from django.core.management import call_command
from django.conf import settings

from celery import shared_task
from redis import Redis

import logging
import time
import random


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
    """
    Entry point task for processing bot operations. This task acquires a lock to ensure that only
    one instance of a bot's task is running at any given time. It also introduces a random delay
    to stagger the execution of tasks for different bots, reducing the likelihood of concurrent
    execution issues.

    Args:
        self: Reference to the task instance.
        bot_id (int): The unique identifier of the bot being processed.
    """

    redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

    # Create a lock specific to the bot_id to ensure no two tasks for the same bot run simultaneously
    lock = redis_client.lock(f"bot_lock_{bot_id}", timeout=300)

     # Attempt to acquire the lock. If it fails, it means another task is already running for this bot
    if lock.acquire(blocking=False):
        try:
            # Introduce a random delay between 5 and 10 seconds to stagger the start of bot tasks.
            # This helps in avoiding concurrent execution and reduces potential resource contention.
            delay = random.uniform(5, 10) # Adding random delay between bot tasks. Maybe can be improved?
            time.sleep(delay)

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
        finally:
            # Release the lock once all tasks for the bot have been completed
            lock.release()
    else:
        logger.warning(f'Bot {bot_id} is already being processed.')


@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def sync_bot_tasks_with_bots(self):
    call_command('sync_bots_with_bot_tasks')

@shared_task(base=CustomExceptionHandler, bind=True, queue='scheduling_queue')
def accept_info_mail_invites(self):
    accept_invite_logger.debug(f'Starting invites processing for info@contxts.net ......')
    call_command('accept_invites', is_accept_invite=True)

