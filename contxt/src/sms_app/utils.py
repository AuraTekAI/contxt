
from core.models import Contact
from sms_app.models import SMS

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import re
from drf_yasg import openapi


def get_to_number_from_message_body(message_body=None):
    if not message_body:
        return None

    # Define a pattern that includes an optional '+' at the start, followed by 10 to 15 digits
    phone_pattern = re.compile(r'\+?\d{10,15}\b')

    # Search for a match in the message body
    match = phone_pattern.search(message_body)

    if not match:
        return None

    to_number = match.group()

    # Ensure that after removing any leading '+', the number is composed entirely of digits
    if not to_number.lstrip('+').isdigit():
        return None

    # Check the length of the number after removing the '+', should be between 10 and 15 digits
    if len(to_number.lstrip('+')) not in range(10, 16):
        return None

    return to_number

def log_sms_to_database(contact_id, message_body, text_id, to_number, direction, status, is_processed, email):
    contact = Contact.objects.filter(id=contact_id).first()
    SMS.objects.create(
        contact = contact,
        email = email,
        message = message_body,
        text_id = text_id,
        phone_number = to_number,
        direction = direction,
        status = status,
        is_processed = is_processed
    )

def log_incoming_request(request, logger):
    logger.debug(f'----------------------------------------------')
    logger.debug(f'HTTP Method: {request.method}')
    logger.debug(f'Headers: {dict(request.headers)}')
    logger.debug(f'Query Params: {request.query_params}')
    logger.debug(f'Body: {request.body.decode("utf-8")}')
    logger.debug(f'Request Data: {request.data}')
    logger.debug(f'----------------------------------------------')

def generate_webhook_token(data):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    return serializer.dumps(data, salt=settings.SECRET_KEY)


def validate_webhook_token(token, max_age=86400):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        data = serializer.loads(token, salt=settings.SECRET_KEY, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    return data


def get_webhook_schema():
    schema_properties = {
        'textId': openapi.Schema(type=openapi.TYPE_STRING, description='The unique identifier for the SMS'),
        'fromNumber': openapi.Schema(type=openapi.TYPE_STRING, description='The phone number from which the SMS was sent'),
        'text': openapi.Schema(type=openapi.TYPE_STRING, description='The content of the SMS'),
    }

    # Conditionally add the 'data' field based on TEST_MODE
    if not settings.TEST_MODE:
        schema_properties['data'] = openapi.Schema(type=openapi.TYPE_STRING, description='Authentication token for validating the webhook')

    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=schema_properties,
        required=['textId', 'fromNumber', 'text'] if not settings.TEST_MODE else ['textId', 'fromNumber', 'text']
    )

def send_quota_limit_reached_notification(quota_limit):
    """
    Sends an email notification to a user when they have reached their quota limit.

    Args:
        quota_limit (int): The quota limit that has been reached.

    Returns:
        None
    """
    user_name = settings.ADMIN_EMAIL_NAME
    to_email = settings.ADMIN_EMAIL_ADDRESS

    subject = 'Quota Limit Reached'

    html_message = render_to_string('emails/quota_limit_reached_notification_email.html', {
        'user_name': user_name,
        'quota_limit': quota_limit
    })
    plain_message = strip_tags(html_message)

    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [to_email]

    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
