
from core.models import Contact
from sms_app.models import SMS

from django.conf import settings

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


def validate_webhook_token(token, max_age=3600):
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

