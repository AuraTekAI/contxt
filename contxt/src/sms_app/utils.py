
from core.models import Contact
from sms_app.models import SMS

import re

def get_to_number_from_message_body(message_body=None):
    if not message_body:
        return None

    cleaned_body = re.sub(r'[^\d]', '', message_body)

    phone_pattern = re.compile(r'\b\d{10}\b')

    match = phone_pattern.search(cleaned_body)

    if not match:
        return None

    to_number = match.group()

    if not to_number.isdigit():
        return None

    if len(to_number) != 10:
        return None


    # This check is specific to US number. This can be expanded to add support for other countries as well.
    if not to_number.startswith(('2', '3', '4', '5', '6', '7', '8', '9')):
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

