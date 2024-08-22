
from accounts.models import User

from django.conf import settings


import logging


pull_email_logger = logging.getLogger('pull_email')


def get_or_create_user(email_data=None):
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
    if settings.USE_ALTERNATE_LOGIN_DETAILS:
        user_name = settings.ALTERNATE_USERNAME
        password = settings.ALTERNATE_PASSWORD
    else:
        user_name = settings.USERNAME
        password = settings.PASSWORD

    return [user_name, password]

