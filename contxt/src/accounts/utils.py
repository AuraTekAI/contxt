
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

def get_email_password_url(bot_id=None):
    """
    Retrieves email credentials based on the provided bot ID.

    This function fetches the email address and password associated with a given bot ID
    from the database. The function ensures that the `bot_id` is provided, and if a
    corresponding bot account is found, it returns the associated email address and password.

    Args:
        bot_id (int, optional): The unique identifier for the bot. This parameter is
        required to fetch the corresponding email credentials.

    Returns:
        tuple: A tuple containing the email address, password and email url associated with the bot ID.
               If the `bot_id` is None or no bot account is found, it returns a tuple
               with all values set to `None`.

    Raises:
        ValueError: If `bot_id` is None, an error message is printed and the function
        returns a tuple with all values set to `None`.
    """
    email_address = None
    email_url = None
    password = None

    if bot_id == None:
        print(f'{bot_id}. bot_id cannot be null')
        return email_address, password, email_url

    bot_obj = BotAccount.objects.filter(id=bot_id).first()
    if bot_obj:
        email_address = bot_obj.email_address
        password = bot_obj.email_password
        email_url = bot_obj.email_url

    return email_address, password, email_url


def get_username_password(bot_id=None):
    """
    Retrieves login credentials based on the configuration settings.

    Depending on whether alternate login details are used, this function returns a list containing
    the username and password for authentication.

    Returns:
        list: A list containing the username and password.
    """
    email_address = None
    password = None

    if bot_id == None:
        print(f'{bot_id}. bot_id cannot be null')
        return email_address, password

    bot_obj = BotAccount.objects.filter(id=bot_id).first()
    if bot_obj:
        email_address = bot_obj.email_address
        password = bot_obj.corrlinks_password

    return email_address, password

