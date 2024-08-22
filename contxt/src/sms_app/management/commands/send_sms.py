from django.core.management.base import BaseCommand
import threading
import logging
import requests
import time
from variables import *
from db_ops import get_database_connection, close_database_resources, log_sms_to_db, update_sms_status_in_db, get_unprocessed_sms, update_sms_processed, get_user_info_by_contact_id, get_contact_by_phone
from push_email import process_emails

console = logging.StreamHandler()
console.setLevel(logging.INFO)

logger = logging.getLogger('send_sms')


class Command(BaseCommand):
    help = 'Process and send SMS messages'

    def handle(self, *args, **kwargs):
        logger.info("Starting SMS processing")
        process_sms_replies()
        quota = check_quota(API_KEY)
        if quota is not None:
            logger.info(f"Current SMS quota: {quota}")
        logger.info("SMS processing completed")


def send_sms_threaded(user_id=None, contact_id=None, to_number=None, message_body=None, message_id=None):
    def send_sms():
        nonlocal user_id, contact_id, to_number, message_body

        logger.debug(f"Starting SMS send process for user_id: {user_id}, contact_id: {contact_id}")

        if TEST_MODE:
            to_number = to_number or TEST_TO_NUMBER
            message_body = message_body or TEST_MESSAGE_BODY
            key = TEST_KEY
            user_id = user_id or TEST_USER_ID
        else:
            key = API_KEY

        if user_id is None or contact_id is None or to_number is None or message_body is None:
            connection, cursor = get_database_connection()
            if connection and cursor:
                try:
                    if user_id is None:
                        cursor.execute("""
                            SELECT TOP 1 UserID, Body
                            FROM Emails
                            WHERE Processed = 'N'
                            ORDER BY SentDateTime DESC
                        """)
                        result = cursor.fetchone()
                        if result:
                            user_id, message_body = result
                            logger.debug(f"Fetched user_id: {user_id} and message body from unprocessed email")
                        else:
                            logger.error("No unprocessed emails found")
                            return

                    contact = get_contact_by_phone(connection, user_id, to_number)
                    contact_id = contact['ContactID'] if contact else 12
                    contact_name = contact['ContactName'] if contact else "Unknown"
                    to_number = contact['PhoneNumber'] if contact else to_number
                    logger.debug(f"Contact details: ID={contact_id}, Name={contact_name}, Number={to_number}")
                finally:
                    close_database_resources(connection, cursor)
            else:
                logger.error("Failed to establish database connection")
                return

        payload = {
            'phone': to_number,
            'message': message_body,
            'key': key,
            'replyWebhookUrl': REPLY_WEBHOOK_URL
        }

        try:
            response = requests.post(SMS_SEND_URL, data=payload)
            result = response.json()

            if result.get('success'):
                text_id = result.get('textId')
                quota_remaining = result.get('quotaRemaining')
                logger.info(f"Message sent successfully. Quota remaining: {quota_remaining}. Text ID: {text_id}")

                with open('sms_quota.log', 'a') as quota_file:
                    quota_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Quota remaining: {quota_remaining}\n")

                connection, cursor = get_database_connection()
                if connection and cursor:
                    try:
                        log_sms_to_db(cursor, contact_id, message_body, "Sent", text_id, to_number, "Outbound")
                        connection.commit()
                        logger.debug(f"SMS logged for contact: {contact_name}")
                    finally:
                        close_database_resources(connection, cursor)

                threading.Timer(SMS_RETRY_DELAY, check_sms_status,
                                args=(text_id, user_id, message_id, message_body, to_number, contact_id)).start()
            else:
                error = result.get('error')
                logger.error(f"Failed to send message. Error: {error}")
                connection, cursor = get_database_connection()
                if connection and cursor:
                    try:
                        log_sms_to_db(cursor, contact_id, message_body, "Failed", None, to_number, "Outbound")
                        connection.commit()
                    finally:
                        close_database_resources(connection, cursor)
        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}")

    threading.Thread(target=send_sms).start()


def check_sms_status(text_id, user_id, message_id, message_body, to_number, contact_id, retry_count=0):
    try:
        response = requests.get(SMS_STATUS_URL.format(text_id))
        result = response.json()
        status = result.get('status')

        logging.debug(f"SMS {text_id} status check: {status}")

        connection, cursor = get_database_connection()
        if connection and cursor:
            try:
                if status == "DELIVERED":
                    update_sms_status_in_db(cursor, text_id, "Delivered")
                    connection.commit()
                    logger.info(f"SMS {text_id} delivered successfully.")
                else:
                    logger.warning(f"SMS {text_id} not delivered. Status: {status}")
                    if retry_count < MAX_SMS_RETRIES:
                        logger.info(f"Retrying SMS send. Attempt {retry_count + 1}")
                        send_sms_threaded(user_id, contact_id, to_number, message_body, message_id)
                        check_sms_status(text_id, user_id, message_id, message_body, to_number, contact_id, retry_count + 1)
                    else:
                        update_sms_status_in_db(cursor, text_id, "Failed")
                        connection.commit()
                        logger.error(f"SMS {text_id} failed after {MAX_SMS_RETRIES} attempts.")
                        send_failure_notification_email(user_id, to_number, contact_id)
            finally:
                close_database_resources(connection, cursor)
    except requests.RequestException as e:
        logger.error(f"Failed to check SMS status: {str(e)}")


def send_failure_notification_email(user_id, to_number, contact_id):
    subject = "SMS Delivery Failure Notification"
    body = f"We were unable to deliver your SMS to {to_number}. Please try again later or contact support if the problem persists."
    process_emails(user_id, subject, body)
    logger.info(f"Sent failure notification email to user {user_id}")


def process_sms_replies():
    unprocessed_sms = get_unprocessed_sms()
    for sms in unprocessed_sms:
        sms_id, contact_id, message, text_id, number = sms
        send_email_reply(contact_id, message, text_id, number)


def send_email_reply(contact_id, message, text_id, number):
    user_info = get_user_info_by_contact_id(contact_id)

    if user_info:
        user_id, user_name, contact_name = user_info
        subject = f"SMS from {contact_name}"
        body = f"Message from {contact_name} ({number}):\n\n{message}"

        if process_emails(user_id, subject, body):
            update_sms_processed(text_id)
            logger.info(f"Email reply sent to user {user_id} for SMS from {contact_name}")
        else:
            logger.error(f"Failed to send email reply for SMS {text_id}")
    else:
        logger.error(f"User info not found for contact ID {contact_id}")


def check_quota(api_key):
    try:
        response = requests.get(SMS_QUOTA_URL.format(api_key))
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


def handle_long_email_reply(user_id, subject, body):
    if len(body) > 13000:
        parts = [body[i:i+13000] for i in range(0, len(body), 13000)]
        for i, part in enumerate(parts):
            if i == 0:
                process_emails(user_id, subject, part)
            else:
                continued_subject = f"{subject} - Cont. ({i+1}/{len(parts)})"
                process_emails(user_id, continued_subject, part)
        logger.info(f"Long email reply split into {len(parts)} parts for user {user_id}")
    else:
        process_emails(user_id, subject, body)
