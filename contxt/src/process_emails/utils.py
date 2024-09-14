
from process_emails.models import Email
from process_emails.tasks import push_new_email_task
from sms_app.models import SMS
from accounts.models import BotAccount
from process_emails.email_processing_service import EmailProcessingHandler
from core.models import ResponseMessages

from django.conf import settings

from datetime import datetime, timedelta
import logging
import pytz
import json


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
            Each dictionary must have the following keys: 'user_id', 'message_id', 'sent_datetime', 'subject', 'body', 'bot_id'.

    Logs:
        - Error if `emails_to_save` is `None`.
        - Error if there is an exception while saving an email to the database.
    """
    if emails_to_save is None:
        pull_email_logger.error('emails_to_save cannot be empty.')
        return None

    bot_id = None  # Variable to hold the bot_id

    for email in emails_to_save:
        try:
            bot_obj = BotAccount.objects.filter(id=email['bot_id']).first()
            if bot_obj:  # Extract bot_id from the first valid email
                bot_id = email['bot_id']
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

    # After saving all emails, run contact management to add, update, and remove contacts
    if bot_id is not None:  # Ensure bot_id is available before passing to EmailProcessingHandler
        try:
            EmailProcessingHandler(bot_id=bot_id)
        except Exception as e:
            pull_email_logger.error(f'Error occurred while processing emails: {e}')
    else:
        pull_email_logger.error('No valid bot_id found in emails_to_save.')


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


def transform_name(name):
    """
    Transforms a name from the format "First Middle Last" to "Last First Middle".

    This function takes a name string where the name is in the format of
    "First Middle Last" (middle name is optional). It then rearranges the
    name components to the format "Last First Middle". If no middle name is
    present, the function will simply return the name as "Last First".

    Parameters:
    ----------
    name : str
        The input name in the format "First Middle Last". The name must
        contain at least a first and last name, separated by spaces.

    Returns:
    -------
    str
        The transformed name in the format "Last First Middle". If no middle
        name is provided, the output will be in the format "Last First".

    Raises:
    ------
    ValueError:
        If the input name has fewer than two parts (i.e., a first and last name).

    Example:
    -------
    >>> transform_name("John Michael Smith")
    'Smith John Michael'

    >>> transform_name("Jane Doe")
    'Doe Jane'
    """

    # Split the input name into parts by spaces
    name_parts = name.split()

    # Ensure that the name has at least two parts (first and last name)
    if len(name_parts) < 2:
        raise ValueError("Name must contain at least a first and last name")

    # Extract the last name (the last part)
    last_name = name_parts[-1]

    # Extract the first name (the first part)
    first_name = name_parts[0]

    # The middle name is everything in between (if it exists)
    middle_name = " ".join(name_parts[1:-1])

    # Rearrange into the "Last First Middle" format
    if middle_name:
        transformed_name = f"{last_name} {first_name} {middle_name}"
    else:
        transformed_name = f"{last_name} {first_name}"

    return transformed_name


def send_welcome_email(is_accept_invite=False, bot_id=None, pic_name='', logger=None):
    """
    Sends a welcome email using a randomly selected bot account.

    This function retrieves a random bot account from the database and sends a welcome email to the recipient
    specified by the `pic_name` parameter. The email content is generated based on a template defined in
    the `ResponseMessages` model, specifically filtering for the message with the `WELCOME_STATUS` key. If
    no bot account is found or no welcome message exists, fallback logic is used.

    Args:
        is_accept_invite (bool, optional): Indicates whether the bot is accepting an invitation. Defaults to False.
        bot_id (int, optional): The ID of the bot executing the task. Defaults to None.
        pic_name (str, optional): The name of the person to whom the welcome email is sent. Defaults to an empty string.

    Returns:
        None: This function doesn't return any value but sends a task to the Celery queue to process the email.

    Workflow:
        1. Retrieves a random bot account from the `BotAccount` model. If no account is found, sets an empty value for the bot account in the message.
        2. Retrieves the welcome message from the `ResponseMessages` model with the `WELCOME_STATUS` key.
        3. Formats the welcome message by injecting the bot account's email address (if available) into the message content.
        4. If no welcome message is found, uses a default fallback message.
        5. Uses the `push_new_email_task` Celery task to send the email message with the generated content and the provided `pic_name`.

    Example:
        send_welcome_email(is_accept_invite=True, bot_id=123, pic_name='John Doe')

    Raises:
        None: No exceptions are raised directly by this function.
    """
    try:
        bot_account = BotAccount.objects.order_by('?').first()
    except Exception as e:
        bot_account = None

    message_args = {}
    if bot_account:
        message_args['bot_account'] = '\n'.join([f"{bot_account.email_address}"])
    else:
        message_args['bot_account'] = ''

    try:
        welcome_message = ResponseMessages.objects.filter(message_key='WELCOME_STATUS').first()
    except Exception as e:
        welcome_message = None

    if welcome_message:
        formatted_message = welcome_message.response_content.format(**message_args)
    else:
        welcome_message = 'Welcome to ConTXT. Something went wrong while sending a message to you. You can send a message to info@contxts.net with subject Support and we will get back to you. Regards Team ConTXT.'
        welcome_message = json.dumps(welcome_message)
        formatted_message = welcome_message

    formatted_message = json.dumps(formatted_message)

    logger.info(f'In utils for sending new email welcome email. message = {formatted_message}. pic_name = {pic_name}. bot_id = {bot_id}. is_accept_invite = {is_accept_invite}')

    pic_name = pic_name
    if not pic_name == None:
        push_new_email_task.delay(pic_name=pic_name, message_content=formatted_message, bot_id=bot_id, is_accept_invite=is_accept_invite)
    else:
        print('Pic number cannot be empty')
