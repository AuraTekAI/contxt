# Import necessary libraries
import threading
import logging
import requests
import time
from variables import *
from db_ops import *
from contact import get_contact_by_phone

# Function to send SMS via Textbelt
def send_sms_threaded(user_id=None):
    """
    Sends an SMS message using Textbelt's service.
    """
    def send_sms():
        nonlocal user_id  # Allow modifying the outer function's user_id

        if TEST_MODE:
            # Use test mode details
            to_number = TEST_TO_NUMBER
            message_body = TEST_MESSAGE_BODY
            key = TEST_KEY
            reply_webhook_url = REPLY_WEBHOOK_URL
            user_id = TEST_USER_ID  # Fixed user ID for debug mode
        else:
            # Use production details
            to_number = PROD_TO_NUMBER
            message_body = PROD_MESSAGE_BODY
            key = API_KEY
            reply_webhook_url = REPLY_WEBHOOK_URL
            
            # Fetch user_id from Email table if not provided
            if user_id is None:
                db_connection, cursor = get_database_connection()
                if db_connection and cursor:
                    try:
                        # Look up the contact
                        contact = get_contact_by_phone(db_connection, user_id, to_number)
                        contact_id = contact['ContactID'] if contact else 12  # Use 12 (UserContactNotFound) if no contact found
                        contact_name = contact['ContactName'] if contact else "Unknown"

                        # Log successful message to the database
                        log_sms_to_db(contact_id=contact_id, message=message_body, status="Sent", text_id=text_id, number=to_number, direction="Outbound")
                        logging.info(f"SMS sent to contact: {contact_name}")

                        # Check SMS status
                        check_sms_status(text_id)
                    finally:
                        cursor.close()
                        db_connection.close()
                else:
                    logging.error("Failed to establish database connection")
                    return

        payload = {
            'phone': to_number,
            'message': message_body,
            'key': key,
            'replyWebhookUrl': reply_webhook_url
        }

        response = requests.post('https://textbelt.com/text', data=payload)
        result = response.json()

        if result.get('success'):
            text_id = result.get('textId')
            logging.info(f"Message sent successfully. Quota remaining: {result.get('quotaRemaining')}. Text ID: {text_id}")
        
            # Get database connection
            db_connection, cursor = get_database_connection()
            
            if db_connection and cursor:
                try:
                    # Look up the contact
                    contact = get_contact_by_phone(db_connection, user_id, to_number)
                    contact_id = contact['ContactID'] if contact else None
                    contact_name = contact['ContactName'] if contact else "Unknown"
            
                    # Log successful message to the database
                    log_sms_to_db(contact_id=contact_id, message=message_body, status="Sent", text_id=text_id, number=to_number, direction="Outbound")
                    logging.info(f"SMS sent to contact: {contact_name}")
            
                    # Check SMS status
                    check_sms_status(text_id)
                finally:
                    cursor.close()
                    db_connection.close()
            else:
                logging.error("Failed to establish database connection")
        else:
            error = result.get('error')
            logging.error(f"Failed to send message. Error: {error}")
            # Log failed message to the database with error status
            log_sms_to_db(contact_id=None, message=message_body, status="Failed", text_id=None, number=to_number, direction="Outbound")

    # Start the threaded SMS sending process
    threading.Thread(target=send_sms).start()

def process_sms_replies():
    """
    Processes incoming SMS replies and sends email responses.
    """
    db_connection, cursor = get_database_connection()
    if not db_connection or not cursor:
        logging.error("Failed to establish database connection")
        return

    try:
        cursor.execute("""
            SELECT SMSID, ContactID, Message, TextID, Number
            FROM SMS
            WHERE Direction = 'Inbound' AND Processed = 'N'
        """)
        replies = cursor.fetchall()

        for reply in replies:
            sms_id, contact_id, message, text_id, number = reply
            send_email_reply(contact_id, message, text_id, number)
            
            # Mark SMS as processed
            cursor.execute("UPDATE SMS SET Processed = 'Y' WHERE SMSID = ?", (sms_id,))
            db_connection.commit()

    finally:
        close_database_resources(db_connection, cursor)

def send_email_reply(contact_id, message, text_id, number):
    """
    Sends an email reply for an incoming SMS.
    """
    db_connection, cursor = get_database_connection()
    if not db_connection or not cursor:
        logging.error("Failed to establish database connection")
        return

    try:
        # Get user and contact information
        cursor.execute("""
            SELECT u.UserID, u.Name, c.ContactName
            FROM Users u
            JOIN Contacts c ON u.UserID = c.UserID
            WHERE c.ContactID = ?
        """, (contact_id,))
        user_info = cursor.fetchone()

        if user_info:
            user_id, user_name, contact_name = user_info
            subject = f"SMS from {contact_name}"
            body = f"Message from {contact_name} ({number}):\n\n{message}"

            # TODO: Implement email sending logic here
            # This might involve calling a function from another module, e.g.:
            # send_email_response(user_id, subject, body)

            logging.info(f"Email reply sent to user {user_id} for SMS from {contact_name}")
        else:
            logging.error(f"User info not found for contact ID {contact_id}")

    finally:
        close_database_resources(db_connection, cursor)

def check_sms_status(text_id, user_id, message_id):
    """
    Checks the delivery status of an SMS and updates the database.
    """
    response = requests.get(f'https://textbelt.com/status/{text_id}')
    result = response.json()
    status = result.get('status')

    if status == "DELIVERED":
        update_sms_status_in_db(text_id, "Delivered")
    else:
        logging.warning(f"SMS {text_id} not delivered. Status: {status}")
        # TODO: Implement retry logic here

def check_quota(api_key):
    response = requests.get(f'https://textbelt.com/quota/{api_key}')
    result = response.json()
    if result.get('success'):
        print(f"Quota remaining: {result.get('quotaRemaining')}")
    else:
        print("Failed to check quota.")
    return result

# Example usage:
# check_quota(API_KEY)

# TODO: Implement function to handle long email replies (over 13000 characters)
def handle_long_email_reply(user_id, subject, body):
    """
    Handles email replies that exceed the 13000 character limit.
    """
    # Implementation pending
    pass