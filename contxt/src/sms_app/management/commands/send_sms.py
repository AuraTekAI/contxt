
from process_emails.models import Email
from core.models import Contact
from sms_app.models import SMS
from accounts.models import User, BotAccount
from sms_app.utils import get_to_number_from_message_subject, log_sms_to_database, generate_webhook_token
from sms_app.tasks import send_quota_limit_reached_email_task
from contxt.utils.constants import SMS_DIRECTION_CHOICES, SMS_STATUS_CHOICES, CURRENT_TASKS_RUN_BY_BOTS

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command

import logging
import requests
import time


SMS_STATUS_CHOICES_DICT = dict(SMS_STATUS_CHOICES)
SMS_DIRECTION_CHOICES_DICT = dict(SMS_DIRECTION_CHOICES)

class Command(BaseCommand):
    help = 'Process and send SMS messages'
    command_name = CURRENT_TASKS_RUN_BY_BOTS['send_sms']

    def add_arguments(self, parser):
        parser.add_argument('--bot_id', type=int, help='The bot id for the bot executing tasks.')

    def handle(self, *args, **kwargs):

        bot_id = kwargs.get('bot_id')
        if bot_id:
            logger = logging.getLogger(f'bot_{bot_id}_{self.command_name}')
        else:
            logger = logging.getLogger('send_sms')

        sms_quota_logger = logging.getLogger('sms_quota')

        logger.info("Starting SMS processing")
        logger.info(f'Send sms got bot id = {bot_id} ')

        quota = self.check_quota(settings.API_KEY, logger=sms_quota_logger)
        if quota is not None:
            sms_quota_logger.info(f"Current SMS quota: {quota}")
            if quota == 0 or quota == 100:
                send_quota_limit_reached_email_task.delay(quota)
            else:
                logger.info(f"SMS sending process Started for bot = {bot_id}")

                self.send_sms(logger=logger, sms_quota_logger=sms_quota_logger, bot_id=bot_id)

                logger.info("SMS processing completed")
        else:
            sms_quota_logger.error('Error occured while getting quota value from textbelt. Skipping execution of send sms.')

    def send_sms(self, user_id=None, contact_id=None, to_number=None, message_body=None, message_id=None, logger=None, sms_quota_logger=None, bot_id=None):
        if user_id and contact_id:
            logger.debug(f"Starting SMS send process for user_id: {user_id}, contact_id: {contact_id}")

        if settings.TEST_MODE:
            to_number = to_number or settings.TEST_TO_NUMBER
            message_body = message_body or settings.TEST_MESSAGE_BODY
            key = settings.API_KEY
            user_id = user_id or settings.TEST_USER_ID

            user_obj = User.objects.filter(pic_number=user_id).first()
            contact = Contact.objects.filter(user=user_obj).first()
            if contact:
                contact_id = contact.id
            else:
                logger.error('No contacts found in the database. Please run seeders to ensure there is at least one contact available for testing.')
            email = Email.objects.filter(user=user_obj).first()

            payload = {
                'phone': to_number,
                'message': message_body,
                'key': key,
                'replyWebhookUrl': settings.REPLY_WEBHOOK_URL,
                'webhookData' : generate_webhook_token({"timestamp": int(time.time())})
            }
            try:
                response = requests.post(settings.SMS_SEND_URL, data=payload)
                result = response.json()

                if result.get('success'):
                    text_id = result.get('textId')
                    quota_remaining = result.get('quotaRemaining')

                    logger.info(f"Message sent successfully. Quota remaining: {quota_remaining}. Text ID: {text_id}")
                    sms_quota_logger.debug(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Quota remaining: {quota_remaining}\n")

                    try:
                        log_sms_to_database(contact_id=contact_id, message_body=message_body, text_id=text_id, to_number=to_number, \
                            direction=SMS_DIRECTION_CHOICES_DICT['Outbound'], status=SMS_STATUS_CHOICES_DICT['Sent'], is_processed=True, email=email)
                        self.check_sms_status(text_id, user_id, message_id, message_body, to_number, contact_id, email=email, logger=logger, sms_quota_logger=sms_quota_logger, bot=None)
                    except Exception as e:
                        logger.error(f'Error occured while logging sms to DB. {e}')

                else:
                    error = result.get('error')
                    logger.error(f"Failed to send message. Error: {error}")
                    try:
                        log_sms_to_database(contact_id=contact_id, message_body=message_body, text_id=None, to_number=to_number,
                            direction=SMS_DIRECTION_CHOICES_DICT['Outbound'], status=SMS_STATUS_CHOICES_DICT['Failed'], is_processed=True, email=email)

                        email.is_processed = True
                        email.save()
                    except Exception as e:
                        logger.error(f'Error occured while logging sms to DB. {e}')
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
        else:
            key = settings.API_KEY

            bot_obj = None
            if bot_id:
                bot_obj = BotAccount.objects.filter(id=bot_id).first()

            unprocessed_emails = Email.objects.filter(is_processed=False, bot=bot_obj).all()

            for email in unprocessed_emails:
                user_id = email.user_id
                message_body = email.body
                subject = email.subject

                to_number = get_to_number_from_message_subject(subject)

                contact = Contact.objects.filter(user_id=user_id, phone_number=to_number).first()
                if not contact and to_number:
                    contact, created = Contact.objects.update_or_create(
                        email = f'{email.user.user_name}@gmail.com',
                        defaults={
                            'user': email.user,
                            'contact_name': f'{email.user.user_name}_{to_number}',
                            'phone_number' : to_number
                        }
                    )
                elif not to_number:
                    logger.error(f'Got an invalid number {subject}.')
                    contact = None

                if contact:
                    contact_id = contact.id
                    contact_name = contact.contact_name
                    to_number = contact.phone_number
                    logger.debug(f"Contact details: ID={contact_id}, Name={contact_name}, Number={to_number}")

                    payload = {
                        'phone': to_number,
                        'message': message_body,
                        'key': key,
                        'replyWebhookUrl': settings.REPLY_WEBHOOK_URL,
                        'webhookData' : generate_webhook_token({"timestamp": int(time.time())})
                    }

                    try:
                        response = requests.post(settings.SMS_SEND_URL, data=payload)
                        result = response.json()

                        if result.get('success'):
                            text_id = result.get('textId')
                            quota_remaining = result.get('quotaRemaining')

                            logger.info(f"Message sent successfully. Quota remaining: {quota_remaining}. Text ID: {text_id}")
                            sms_quota_logger.debug(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Quota remaining: {quota_remaining}\n")

                            try:
                                log_sms_to_database(contact_id=contact_id, message_body=message_body, text_id=text_id, to_number=to_number, \
                                    direction=SMS_DIRECTION_CHOICES_DICT['Outbound'], status=SMS_STATUS_CHOICES_DICT['Sent'], is_processed=True, email=email, bot=bot_obj)
                                self.check_sms_status(text_id, user_id, message_id, message_body, to_number, contact_id, email=email, logger=logger, sms_quota_logger=sms_quota_logger, bot=bot_obj)
                            except Exception as e:
                                logger.error(f'Error occured while logging sms to DB. {e}')
                        else:
                            error = result.get('error')
                            logger.error(f"Failed to send message. Error: {error}")
                            try:
                                log_sms_to_database(contact_id=contact_id, message_body=message_body, text_id=None, to_number=to_number, \
                                    direction=SMS_DIRECTION_CHOICES_DICT['Outbound'], status=SMS_STATUS_CHOICES_DICT['Failed'], is_processed=True, email=email, bot=bot_obj)

                                email.is_processed = True
                                email.save()
                            except Exception as e:
                                logger.error(f'Error occured while logging sms to DB. {e}')
                    except requests.RequestException as e:
                        logger.error(f"Request failed: {str(e)}")
                else:
                    logger.error(f'No contact found in database for number {to_number}. Also the number might be invalid so skipping saving it in database or sending sms')

    def check_sms_status(self, text_id, user_id, message_id, message_body, to_number, contact_id, retry_count=0, email=None, logger=None, sms_quota_logger=None, bot=None):
        try:
            '''
            This currently has to be executed with delay because on textbelt side, the status of SMS is updated with delay.
            For example a SMS maybe delievered successfuly but their api still return SENT instead of DELIVERED.
            '''
            response = None
            for retry in range(settings.MAX_SMS_RETRIES):
                time.sleep(settings.SMS_RETRY_DELAY)
                response = requests.get(settings.SMS_STATUS_URL.format(text_id))
                response.raise_for_status()

                result = response.json()
                if result.get('status') == "DELIVERED":
                    break

            status = result.get('status')

            logger.debug(f"SMS {text_id} status check: {status}")

            sms_obj = SMS.objects.filter(text_id=text_id, direction=SMS_DIRECTION_CHOICES_DICT['Outbound']).first()
            if not sms_obj:
                logger.error(f"SMS object with text_id {text_id} not found in database.")
                return

            if status == "DELIVERED":
                sms_obj.status = SMS_STATUS_CHOICES_DICT['Delivered']
                sms_obj.save()

                email.is_processed = True
                email.save()

                logger.info(f"SMS {text_id} delivered successfully.")
            else:
                logger.warning(f"SMS {text_id} not delivered. Status: {status}")

                if retry_count < settings.MAX_SMS_RETRIES:
                    sms_obj.status = SMS_STATUS_CHOICES_DICT['Unknown']
                    sms_obj.save()

                    logger.info(f"Retrying SMS send. Attempt {retry_count + 1}")
                    time.sleep(settings.SMS_RETRY_DELAY)

                    # Attempt to resend the SMS
                    new_text_id = self.resend_sms(user_id, contact_id, to_number, message_body, retry_count,email=email, logger=logger, sms_quota_logger=sms_quota_logger, bot=bot)

                    if new_text_id:
                        self.check_sms_status(new_text_id, user_id, message_id, message_body, to_number, contact_id, retry_count + 1, email=email, logger=logger, sms_quota_logger=sms_quota_logger, bot=bot)
                else:
                    sms_obj.status = SMS_STATUS_CHOICES_DICT['Failed']
                    sms_obj.save()

                    email.is_processed = True
                    email.save()

                    logger.error(f"SMS {text_id} failed after {settings.MAX_SMS_RETRIES} attempts.")
                    self.send_failure_notification_email(user_id, to_number, email.message_id, logger=logger)

        except requests.RequestException as e:
            logger.warning(f"SMS {text_id} not delivered. Status: {status}")

            if retry_count < settings.MAX_SMS_RETRIES:
                sms_obj.status = SMS_STATUS_CHOICES_DICT['Unknown']
                sms_obj.save()

                logger.info(f"Retrying SMS send. Attempt {retry_count + 1}")
                time.sleep(settings.SMS_RETRY_DELAY)

                # Attempt to resend the SMS
                new_text_id = self.resend_sms(user_id, contact_id, to_number, message_body, retry_count,email=email, logger=logger, sms_quota_logger=sms_quota_logger, bot=bot)

                if new_text_id:
                    self.check_sms_status(new_text_id, user_id, message_id, message_body, to_number, contact_id, retry_count + 1, email=email, bot=bot, logger=logger, sms_quota_logger=sms_quota_logger)
            else:
                sms_obj.status = SMS_STATUS_CHOICES_DICT['Failed']
                sms_obj.save()

                email.is_processed = True
                email.save()

                logger.error(f"SMS {text_id} failed after {settings.MAX_SMS_RETRIES} attempts.")
                self.send_failure_notification_email(user_id, to_number, email.message_id, logger=logger)

        except Exception as e:
            logger.error(f"An error occurred while checking status of the sent SMS {text_id}. Error = {e}")

    def resend_sms(self, user_id, contact_id, to_number, message_body, retry_count, email, logger, sms_quota_logger, bot=None):
        logger.info(f"Resending SMS. Retry Count: {retry_count}")

        payload = {
            'phone': to_number,
            'message': message_body,
            'key': settings.API_KEY,
            'replyWebhookUrl': settings.REPLY_WEBHOOK_URL,
            'webhookData' : generate_webhook_token({"timestamp": int(time.time())})
        }

        try:
            response = requests.post(settings.SMS_SEND_URL, data=payload)
            result = response.json()

            if result.get('success'):
                new_text_id = result.get('textId')
                quota_remaining = result.get('quotaRemaining')

                logger.info(f"Message resent successfully. New Text ID: {new_text_id}. Quota remaining: {quota_remaining}")
                sms_quota_logger.debug(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Quota remaining: {quota_remaining}\n")

                log_sms_to_database(contact_id=contact_id, message_body=message_body, text_id=new_text_id, to_number=to_number,
                    direction=SMS_DIRECTION_CHOICES_DICT['Outbound'], status=SMS_STATUS_CHOICES_DICT['Sent'], is_processed=True, email=email, bot=bot)

                return new_text_id

            else:
                error = result.get('error')
                logger.error(f"Failed to resend message. Error: {error}")
                log_sms_to_database(contact_id=contact_id, message_body=message_body, text_id=None, to_number=to_number,
                    direction=SMS_DIRECTION_CHOICES_DICT['Outbound'], status=SMS_STATUS_CHOICES_DICT['Failed'], is_processed=True, email=email)
                return None

        except requests.RequestException as e:
            logger.error(f"Resend request failed: {str(e)}")
            return None

    # TODO make this better
    def send_failure_notification_email(self, user_id, to_number, message_id, logger):
        subject = "SMS Delivery Failure Notification\n"
        body = f"We were unable to deliver your SMS to {to_number}. Please try again later or contact support if the problem persists."

        message_content = subject + body

        call_command('push_emails', message_id=message_id, message_content=message_content)
        logger.info(f"Sent failure notification email to user {user_id}")

    def check_quota(self, api_key, logger):
        try:
            response = requests.get(settings.SMS_QUOTA_URL.format(api_key))
            result = response.json()
            if result.get('success'):
                quota_remaining = result.get('quotaRemaining')
                logger.info(f"Quota remaining: {quota_remaining}")
                return quota_remaining
            else:
                logger.error("Failed to check quota.")
                return None
        except requests.RequestException as e:
            logger.error(f"Error checking quota: {str(e)}")
            return None

    # Leaving this here as a reminder to include this logic in push email
    def handle_long_email_reply(self, user_id, subject, body, logger):
        if len(body) > 13000:
            parts = [body[i:i + 13000] for i in range(0, len(body), 13000)]
            for i, part in enumerate(parts):
                if i == 0:
                    # process_emails(user_id, subject, part) # TODO implement this
                    pass
                else:
                    continued_subject = f"{subject} - Cont. ({i + 1}/{len(parts)})"
                    # process_emails(user_id, continued_subject, part) # TODO implement this
            logger.info(f"Long email reply split into {len(parts)} parts for user {user_id}")
        else:
            # process_emails(user_id, subject, body) # TODO implement this
            pass
