
from process_emails.models import Email
from sms_app.models import SMS
from accounts.models import BotAccount
from process_emails.email_processing_service import EmailProcessingHandler

from django.conf import settings

from datetime import datetime, timedelta
import logging
import pytz


pull_email_logger = logging.getLogger('pull_email')

def convert_string_to_valid_datetime(datetime_string=None, timezone=settings.TIME_ZONE):
    """
    Converts a string representation of a datetime to a formatted string with timezone information.

    Args:
        datetime_string (str, optional): The datetime string to convert, formatted as "%m/%d/%Y %I:%M:%S %p".
        timezone (str, optional): The timezone to localize the datetime to. Defaults to the timezone specified in settings.

    Returns:
        str: The formatted datetime string with timezone information, or None if the input is invalid.

    Logs:
        - Error if `datetime_string` is `None`.
    """
    if datetime_string is None:
        pull_email_logger.error('datetime_string cannot be NULL')
        return None

    try:
        parsed_datetime = datetime.strptime(datetime_string, "%m/%d/%Y %I:%M:%S %p")
    except ValueError as e:
        pull_email_logger.error(f'Error parsing datetime string: {e}')
        return None

    local_tz = pytz.timezone(timezone)
    aware_datetime = local_tz.localize(parsed_datetime)

    formatted_date = aware_datetime.strftime("%Y-%m-%d %H:%M:%S %z")

    return formatted_date

def save_emails(emails_to_save=None):
    """
    Saves a list of email records to the database.

    Args:
        emails_to_save (list of dicts, optional): List of dictionaries, each containing email details to be saved.
            Each dictionary must have the following keys: 'user_id', 'message_id', 'sent_datetime', 'subject', 'body'.

    Logs:
        - Error if `emails_to_save` is `None`.
        - Error if there is an exception while saving an email to the database.
    """
    if emails_to_save is None:
        pull_email_logger.error('emails_to_save can not be empty.')
        return None

    for email in emails_to_save:
        try:
            bot_obj = BotAccount.objects.filter(id=email['bot_id']).first()
            Email.objects.create(
                user=email['user_id'],
                message_id=email['message_id'],
                sent_date_time=convert_string_to_valid_datetime(email['sent_datetime']),
                subject=email['subject'],
                body=email['body'],
                bot=bot_obj
            )
        except Exception as e:
            pull_email_logger.error(f'Error occurred while saving Email to database: {email} {e}')

        # after all the emails have been pulled and saved in database, run contact management to add, update and remove contacts
        EmailProcessingHandler(bot_id=5)


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

def get_messages_to_send_from_database(message_id_content=[], bot_id=None):
    """
    Retrieves unprocessed SMS messages from the database and collects corresponding email data.

    Args:
        message_id_content (list of lists, optional): A list to which SMS message details will be appended.
            Each entry in the list will be a sublist containing SMS ID, email message ID, and the SMS message content.

    Returns:
        list of lists: Updated `message_id_content` with details of unprocessed SMS messages and corresponding email data.

    Notes:
        - Filters for SMS messages that are inbound and have not been processed.
        - For each unprocessed SMS, retrieves the associated email object to get the message ID.
        - Appends a list containing SMS ID, email message ID, and message content to `message_id_content` for each unprocessed SMS.
    """
    bot_obj = BotAccount.objects.filter(id=bot_id).first()
    unprocessed_sms_objects = SMS.objects.filter(is_processed=False, direction='Inbound', bot=bot_obj).all()
    if unprocessed_sms_objects:
        for unprocessed_sms in unprocessed_sms_objects:
            email_obj = Email.objects.filter(id=unprocessed_sms.email.id, bot=bot_obj).first()
            if email_obj:
                message_id_content.append([unprocessed_sms.id, email_obj.message_id, unprocessed_sms.message])
    return message_id_content


def update_sms_processed_value(sms_id=None):
    """
    Updates the `is_processed` flag of a specific SMS record to `True` in the database.

    Args:
        sms_id (int, optional): The ID of the SMS record to update.

    Returns:
        bool: `True` if the SMS record was found and updated successfully, otherwise `False`.

    Notes:
        - Retrieves the SMS object with the given `sms_id`.
        - Sets the `is_processed` attribute of the SMS object to `True` and saves the changes.
    """
    sms_object = SMS.objects.filter(id=int(sms_id)).first()
    if sms_object:
        sms_object.is_processed = True
        sms_object.save()

        return True

    return False
