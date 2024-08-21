
from process_emails.models import Email
from core.models import SMS

from django.conf import settings

from datetime import datetime, timedelta
import logging
import pytz


pull_email_logger = logging.getLogger('pull_email')

def convert_string_to_valid_datetime(datetime_string=None, timezone=settings.TIME_ZONE):
    if datetime_string is None:
        pull_email_logger.error('datetime_string cannot be NULL')
        return None

    parsed_datetime = datetime.strptime(datetime_string, "%m/%d/%Y %I:%M:%S %p")

    local_tz = pytz.timezone(timezone)
    aware_datetime = local_tz.localize(parsed_datetime)

    formatted_date = aware_datetime.strftime("%Y-%m-%d %H:%M:%S %z")

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


def convert_cookies_to_splash_format(splash_cookies=None, cookies=None):
    """
    Converts cookies to the format required by Splash.

    Parameters:
    - splash_cookies (list): The list to which formatted cookies will be appended.
    - cookies (dict): The dictionary of cookies to be converted, with cookie names as keys and cookie values as values.

    Returns:
    - list: The updated list of Splash-formatted cookies if both parameters are provided.
    - bool: False if the necessary parameters are not provided.

    This function takes a dictionary of cookies and appends them to a list in a format that can be used by Splash,
    including setting attributes such as name, value, expiration time, path, httpOnly, secure, and domain.
    If either parameter is missing or None, the function returns False.
    """
    if (not splash_cookies == None) and (cookies):
        now = datetime.now()
        expires = now + timedelta(hours=1)
        for name, value in cookies.items():
            cookie = {
                'name': name,
                'value': value,
                'expires': expires.isoformat(),
                'path': '/',
                'httpOnly': True,
                'secure': True,
                'domain': 'www.corrlinks.com'
            }
            splash_cookies.append(cookie)
        return splash_cookies
    else:
        return False

def get_messages_to_send_from_database(message_id_content=[]):
    unprocessed_sms_objects = SMS.objects.filter(is_processed=False, direction='Inbound').all()
    if unprocessed_sms_objects:
        for unprocessed_sms in unprocessed_sms_objects:
            email_obj = Email.objects.filter(id=unprocessed_sms.email.id).first()
            if email_obj:
                message_id_content.append([unprocessed_sms.id, email_obj.message_id, unprocessed_sms.message])
    return message_id_content


def update_sms_processed_value(sms_id=None):
    sms_object = SMS.objects.filter(id=int(sms_id)).first()
    if sms_object:
        sms_object.is_processed = True
        sms_object.save()

    return True
