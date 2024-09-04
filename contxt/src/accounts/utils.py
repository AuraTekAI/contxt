
from accounts.models import User, BotAccount

from django.conf import settings


import logging


pull_email_logger = logging.getLogger('pull_email')


# Currently only two email urls, can keep expanding this as required
MAP_EMAIL_URL_TO_EMAIL_SEARCH_STRINGS = {
    'smtp.gmail.com' : [settings.GMAIL_SEARCH_STRING, settings.GMAIL_BROADER_SEARCH_STRING,],
    'mail.contxts.net' : [settings.CONTXT_MAIL_SEARCH_STRING, settings.CONTXT_MAIL_BROADER_SEARCH_STRING]
}


def get_or_create_user(email_data=None):
    """
    Retrieves or creates a `User` based on the provided email data.

    This function extracts user information from `email_data` and uses it to either fetch an existing user
    or create a new user. The user is identified by `pic_number` (extracted from `email_data`). If the user is created,
    an initial password is set.

    Parameters:
        email_data (dict, optional): Dictionary containing email data with 'from' field that includes user information.

    Returns:
        User: The retrieved or created `User` instance, or `None` if no email data is provided or if an error occurs.

    Logs:
        - Error if `email_data` is `None`.
        - Error if the `user_id_name` format is invalid.
    """
    if email_data is None:
        pull_email_logger.error("No email data provided.")
        return None

    password_value = settings.SUPER_SECRET_INITIAL_USER_PASSWORD
    user_id_name = None
    user_id = None
    name = None

    try:
        user_id_name = email_data.get('from')
        name, user_id = user_id_name.rsplit(' (', 1)
        user_id = user_id.strip(')')
        name = name.strip()
    except ValueError:
        pull_email_logger.error(f"Invalid format for user_name_id: {user_id_name}")
        return None

    user, created = User.objects.get_or_create(
        pic_number=user_id,
        defaults={
            'name': name,
            'is_active': False,
            'user_name': f'{name.replace(" ", "")}_{user_id.replace(" ", "")}'
        }
    )

    if created:
        user.set_password(password_value)
        user.save()

    return user

def get_email_password_url(bot_id=None, is_accept_invite=False):
    """
    Retrieves email credentials and URL based on the provided bot ID or the `is_accept_invite` flag.

    This function fetches the email address, password, and email URL associated with a given bot ID
    from the database. If the `is_accept_invite` flag is set to `True`, it retrieves the credentials
    and URL from the settings. If the flag is `False`, the function looks up the credentials in the
    database using the provided `bot_id`.

    Args:
        bot_id (int, optional): The unique identifier for the bot. This parameter is required to fetch
                                the corresponding email credentials from the database.
        is_accept_invite (bool, optional): A flag to determine whether to use alternate email credentials
                                           from the settings. Defaults to `False`.

    Returns:
        tuple: A tuple containing the email address, password, and email URL associated with the bot ID or
               settings. If the `bot_id` is `None` or no bot account is found, it returns a tuple with all
               values set to `None`.

    Raises:
        ValueError: If `bot_id` is `None` and `is_accept_invite` is `False`, an error message is printed
                    and the function returns a tuple with all values set to `None`.
    """
    email_address = None
    email_url = None
    password = None

    if is_accept_invite:
        email_address = settings.EMAIL_USERNAME
        password = settings.EMAIL_PASSWORD
        email_url = settings.EMAILURL

    else:
        if bot_id == None:
            print(f'{bot_id}. bot_id cannot be null')
            return email_address, password, email_url

        bot_obj = BotAccount.objects.filter(id=bot_id).first()
        if bot_obj:
            email_address = bot_obj.email_address
            password = bot_obj.email_password
            email_url = bot_obj.email_url

    return email_address, password, email_url


def get_username_password(bot_id=None, is_accept_invite=False):
    """
    Retrieves login credentials based on the provided bot ID or a flag indicating whether to use
    alternate credentials for accepting invitations.

    This function checks if the `is_accept_invite` flag is set to `True`. If so, it returns the
    alternate username and password configured in the settings. If the flag is `False`, the function
    retrieves the credentials associated with the provided `bot_id` from the `BotAccount` model.

    Args:
        bot_id (int, optional): The ID of the bot whose credentials need to be retrieved.
                                Defaults to `None`.
        is_accept_invite (bool, optional): A flag to determine whether to use alternate login credentials.
                                           Defaults to `False`.

    Returns:
        tuple: A tuple containing the username (email_address) and password. If the credentials cannot
               be retrieved, both values will be `None`.
    """
    email_address = None
    password = None

    if is_accept_invite:
        email_address = settings.ALTERNATE_USERNAME
        password = settings.ALTERNATE_PASSWORD
    else:
        if bot_id == None:
            print(f'{bot_id}. bot_id cannot be null')
            return email_address, password

        bot_obj = BotAccount.objects.filter(id=bot_id).first()
        if bot_obj:
            email_address = bot_obj.email_address
            password = bot_obj.corrlinks_password

    return email_address, password

