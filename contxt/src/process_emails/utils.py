
from process_emails.models import Email

from django.conf import settings


from datetime import datetime
import logging


pull_email_logger = logging.getLogger('pull_email')

def convert_string_to_valid_datetime(datetime_string=None):
    if datetime_string == None:
        pull_email_logger.error('datetime_string can not be NULL')
        return None

    parsed_datetime = datetime.strptime(datetime_string, "%m/%d/%Y %I:%M:%S %p")

    formatted_date = parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")

    return formatted_date

def save_emails(emails_to_save=None):
    if emails_to_save == None:
        pull_email_logger.error('emails_to_save can not be empty.')
        return None

    for email in emails_to_save:
        try:
            Email.objects.create(user=email['user_id'], message_id=email['message_id'], sent_date_time=convert_string_to_valid_datetime(email['sent_datetime']), subject=email['subject'], body=email['body'])
        except Exception as e:
            pull_email_logger.error(f'Error occured while saving Email to database {email} {e}')
