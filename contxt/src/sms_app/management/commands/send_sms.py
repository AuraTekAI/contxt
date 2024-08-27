
from process_emails.models import Email
from core.models import Contact
from sms_app.models import SMS
from accounts.models import User
from sms_app.utils import get_to_number_from_message_body, log_sms_to_database, generate_webhook_token
from sms_app.tasks import send_quota_limit_reached_email_task
from contxt.utils.constants import SMS_DIRECTION_CHOICES, SMS_STATUS_CHOICES

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command

import logging
import requests
import time

logger = logging.getLogger('send_sms')
sms_quota_logger = logging.getLogger('sms_quota')

SMS_STATUS_CHOICES_DICT = dict(SMS_STATUS_CHOICES)
SMS_DIRECTION_CHOICES_DICT = dict(SMS_DIRECTION_CHOICES)

class Command(BaseCommand):
    help = 'Process and send SMS messages'

    def handle(self, *args, **kwargs):
        logger.info("Starting SMS processing")

        quota = self.check_quota(settings.API_KEY)
        if quota is not None:
            sms_quota_logger.info(f"Current SMS quota: {quota}")
            if quota == 0:
                send_quota_limit_reached_email_task.delay(quota)
            else:
                logger.info("SMS sending process Started")

                self.send_sms()

                logger.info("SMS processing completed")
        else:
            sms_quota_logger.error('Error occured while getting quota value from textbelt. Skipping execution of send sms.')

    def send_sms(self, user_id=None, contact_id=None, to_number=None, message_body=None, message_id=None):
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
                        self.check_sms_status(text_id, user_id, message_id, message_body, to_number, contact_id, email=email)
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
            unprocessed_emails = Email.objects.filter(is_processed=False).all()

            for email in unprocessed_emails:
                user_id = email.user_id
                message_body = email.body

                to_number = get_to_number_from_message_body(message_body)

                contact = Contact.objects.filter(user_id=user_id, phone_number=to_number).first()
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
                                    direction=SMS_DIRECTION_CHOICES_DICT['Outbound'], status=SMS_STATUS_CHOICES_DICT['Sent'], is_processed=True, email=email)
                                self.check_sms_status(text_id, user_id, message_id, message_body, to_number, contact_id, email=email)
                            except Exception as e:
                                logger.error(f'Error occured while logging sms to DB. {e}')
                        else:
                            error = result.get('error')
                            logger.error(f"Failed to send message. Error: {error}")
                            try:
                                log_sms_to_database(contact_id=contact_id, message_body=message_body, text_id=None, to_number=to_number, \
                                    direction=SMS_DIRECTION_CHOICES_DICT['Outbound'], status=SMS_STATUS_CHOICES_DICT['Failed'], is_processed=True, email=email)

                                email.is_processed = True
                                email.save()
                            except Exception as e:
                                logger.error(f'Error occured while logging sms to DB. {e}')
                    except requests.RequestException as e:
                        logger.error(f"Request failed: {str(e)}")
                else:
                    logger.error(f'No contact found in database for number {to_number}.')

    def check_sms_status(self, text_id, user_id, message_id, message_body, to_number, contact_id, retry_count=0, email=None):
        try:
            time.sleep(settings.SMS_RETRY_DELAY)
            response = requests.get(settings.SMS_STATUS_URL.format(text_id))
            response.raise_for_status()
            result = response.json()
            status = result.get('status')

            logger.debug(f"SMS {text_id} status check: {status}")

            sms_obj = SMS.objects.filter(text_id=text_id).first()
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
                    new_text_id = self.resend_sms(user_id, contact_id, to_number, message_body, retry_count,email=email)

                    if new_text_id:
                        self.check_sms_status(new_text_id, user_id, message_id, message_body, to_number, contact_id, retry_count + 1, email=email)
                else:
                    sms_obj.status = SMS_STATUS_CHOICES_DICT['Failed']
                    sms_obj.save()

                    email.is_processed = True
                    email.save()

                    logger.error(f"SMS {text_id} failed after {settings.MAX_SMS_RETRIES} attempts.")
                    self.send_failure_notification_email(user_id, to_number, email.message_id)

        except requests.RequestException as e:
            logger.warning(f"SMS {text_id} not delivered. Status: {status}")

            if retry_count < settings.MAX_SMS_RETRIES:
                sms_obj.status = SMS_STATUS_CHOICES_DICT['Unknown']
                sms_obj.save()

                logger.info(f"Retrying SMS send. Attempt {retry_count + 1}")
                time.sleep(settings.SMS_RETRY_DELAY)

                # Attempt to resend the SMS
                new_text_id = self.resend_sms(user_id, contact_id, to_number, message_body, retry_count,email=email)

                if new_text_id:
                    self.check_sms_status(new_text_id, user_id, message_id, message_body, to_number, contact_id, retry_count + 1, email=email)
            else:
                sms_obj.status = SMS_STATUS_CHOICES_DICT['Failed']
                sms_obj.save()

                email.is_processed = True
                email.save()

                logger.error(f"SMS {text_id} failed after {settings.MAX_SMS_RETRIES} attempts.")
                self.send_failure_notification_email(user_id, to_number, email.message_id)

        except Exception as e:
            logger.error(f"An error occurred while checking status of the sent SMS {text_id}. Error = {e}")

    def resend_sms(self, user_id, contact_id, to_number, message_body, retry_count, email):
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
                    direction=SMS_DIRECTION_CHOICES_DICT['Outbound'], status=SMS_STATUS_CHOICES_DICT['Sent'], is_processed=True, email=email)

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
    def send_failure_notification_email(self, user_id, to_number, message_id):
        subject = "SMS Delivery Failure Notification\n"
        body = f"We were unable to deliver your SMS to {to_number}. Please try again later or contact support if the problem persists."

        message_content = subject + body

        call_command('push_emails', message_id=message_id, message_content=message_content)
        logger.info(f"Sent failure notification email to user {user_id}")

    def check_quota(self, api_key):
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
    def handle_long_email_reply(self, user_id, subject, body):
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
