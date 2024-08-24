
from accounts.models import User

from django.conf import settings


import logging


pull_email_logger = logging.getLogger('pull_email')


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

def get_email_password_url():
    """
    Retrieves email credentials and URL based on the configuration settings.

    Depending on whether alternate email settings are used, this function returns a list containing
    the email username, password, and URL for accessing the email service.

    Returns:
        list: A list containing email username, password, and URL.
    """
    if settings.USE_ALTERNATE_EMAIL:
        user_name = settings.ALTERNATE_EMAIL_USERNAME
        password = settings.ALTERNATE_EMAIL_PASSWORD
        email_Url = settings.ALTERNATE_EMIALURL
    else:
        user_name = settings.EMAIL_USERNAME
        password = settings.EMAIL_PASSWORD
        email_Url = settings.EMAILURL

    return [user_name, password, email_Url]

def get_username_password():
    """
    Retrieves login credentials based on the configuration settings.

    Depending on whether alternate login details are used, this function returns a list containing
    the username and password for authentication.

    Returns:
        list: A list containing the username and password.
    """
    if settings.USE_ALTERNATE_LOGIN_DETAILS:
        user_name = settings.ALTERNATE_USERNAME
        password = settings.ALTERNATE_PASSWORD
    else:
        user_name = settings.USERNAME
        password = settings.PASSWORD

    return [user_name, password]

