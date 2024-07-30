import threading
import logging
import requests
import time
from variables import *
from db_ops import get_database_connection, close_database_resources, log_sms_to_db, update_sms_status_in_db, get_unprocessed_sms, update_sms_processed, get_user_info_by_contact_id, get_contact_by_phone
from push_email import process_emails

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='send_sms.log', filemode='a')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

def send_sms_threaded(user_id=None, contact_id=None, to_number=None, message_body=None, message_id=None):
    """
    Sends an SMS message using Textbelt's service in a separate thread.
    Parameters:
    - user_id (int, optional): The ID of the user sending the SMS
    - contact_id (int, optional): The ID of the contact receiving the SMS
    - to_number (str, optional): The phone number to send the SMS to
    - message_body (str, optional): The content of the SMS
    - message_id (str, optional): A unique identifier for the message

    This function handles the entire SMS sending process, including fetching necessary information
    if not provided, sending the SMS via the Textbelt API, logging the SMS to the database,
    and initiating a status check after sending.
    """
    def send_sms():
        nonlocal user_id, contact_id, to_number, message_body

        logging.debug(f"Starting SMS send process for user_id: {user_id}, contact_id: {contact_id}")

        if TEST_MODE:
            to_number = to_number or TEST_TO_NUMBER
            message_body = message_body or TEST_MESSAGE_BODY
            key = TEST_KEY
            user_id = user_id or TEST_USER_ID
        else:
            key = API_KEY

        # Fetch user_id and contact info if not provided
        if user_id is None or contact_id is None or to_number is None or message_body is None:
            connection, cursor = get_database_connection()
            if connection and cursor:
                try:
                    if user_id is None:
                        cursor.execute("""
                            SELECT TOP 1 UserID, Body
                            FROM Emails
                            WHERE Processed = 'N'
                            ORDER BY SentDateTime DESC
                        """)
                        result = cursor.fetchone()
                        if result:
                            user_id, message_body = result
                            logging.debug(f"Fetched user_id: {user_id} and message body from unprocessed email")
                        else:
                            logging.error("No unprocessed emails found")
                            return

                    contact = get_contact_by_phone(connection, user_id, to_number)
                    contact_id = contact['ContactID'] if contact else 12
                    contact_name = contact['ContactName'] if contact else "Unknown"
                    to_number = contact['PhoneNumber'] if contact else to_number
                    logging.debug(f"Contact details: ID={contact_id}, Name={contact_name}, Number={to_number}")
                finally:
                    close_database_resources(connection, cursor)
            else:
                logging.error("Failed to establish database connection")
                return

        payload = {
            'phone': to_number,
            'message': message_body,
            'key': key,
            'replyWebhookUrl': REPLY_WEBHOOK_URL
        }

        try:
            response = requests.post(SMS_SEND_URL, data=payload)
            result = response.json()

            if result.get('success'):
                text_id = result.get('textId')
                quota_remaining = result.get('quotaRemaining')
                logging.info(f"Message sent successfully. Quota remaining: {quota_remaining}. Text ID: {text_id}")
                
                # Log remaining quota to a separate file
                with open('sms_quota.log', 'a') as quota_file:
                    quota_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Quota remaining: {quota_remaining}\n")
                
                connection, cursor = get_database_connection()
                if connection and cursor:
                    try:
                        log_sms_to_db(cursor, contact_id, message_body, "Sent", text_id, to_number, "Outbound")
                        connection.commit()
                        logging.debug(f"SMS logged for contact: {contact_name}")
                    finally:
                        close_database_resources(connection, cursor)
                
                threading.Timer(SMS_RETRY_DELAY, check_sms_status, 
                                args=(text_id, user_id, message_id, message_body, to_number, contact_id)).start()
            else:
                error = result.get('error')
                logging.error(f"Failed to send message. Error: {error}")
                connection, cursor = get_database_connection()
                if connection and cursor:
                    try:
                        log_sms_to_db(cursor, contact_id, message_body, "Failed", None, to_number, "Outbound")
                        connection.commit()
                    finally:
                        close_database_resources(connection, cursor)
        except requests.RequestException as e:
            logging.error(f"Request failed: {str(e)}")

    threading.Thread(target=send_sms).start()

def check_sms_status(text_id, user_id, message_id, message_body, to_number, contact_id, retry_count=0):
    """
    Checks the delivery status of an SMS and updates the database.
    Parameters:
    - text_id (str): The unique identifier of the SMS
    - user_id (int): The ID of the user who sent the SMS
    - message_id (str): The message ID associated with the SMS
    - message_body (str): The content of the SMS
    - to_number (str): The recipient's phone number
    - contact_id (int): The ID of the contact receiving the SMS
    - retry_count (int, optional): The current retry attempt count

    This function queries the Textbelt API for the status of a sent SMS, updates the database
    with the status, and handles retries or failure notifications as necessary.
    """
    try:
        response = requests.get(SMS_STATUS_URL.format(text_id))
        result = response.json()
        status = result.get('status')

        logging.debug(f"SMS {text_id} status check: {status}")

        connection, cursor = get_database_connection()
        if connection and cursor:
            try:
                if status == "DELIVERED":
                    update_sms_status_in_db(cursor, text_id, "Delivered")
                    connection.commit()
                    logging.info(f"SMS {text_id} delivered successfully.")
                else:
                    logging.warning(f"SMS {text_id} not delivered. Status: {status}")
                    if retry_count < MAX_SMS_RETRIES:
                        logging.info(f"Retrying SMS send. Attempt {retry_count + 1}")
                        send_sms_threaded(user_id, contact_id, to_number, message_body, message_id)
                        check_sms_status(text_id, user_id, message_id, message_body, to_number, contact_id, retry_count + 1)
                    else:
                        update_sms_status_in_db(cursor, text_id, "Failed")
                        connection.commit()
                        logging.error(f"SMS {text_id} failed after {MAX_SMS_RETRIES} attempts.")
                        send_failure_notification_email(user_id, to_number, contact_id)
            finally:
                close_database_resources(connection, cursor)
    except requests.RequestException as e:
        logging.error(f"Failed to check SMS status: {str(e)}")

def send_failure_notification_email(user_id, to_number, contact_id):
    """
    Sends a notification email to the user about SMS delivery failure.
    Parameters:
    - user_id (int): The ID of the user to notify
    - to_number (str): The phone number that failed to receive the SMS
    - contact_id (int): The ID of the contact associated with the failed SMS

    This function composes and sends an email to the user informing them about the
    failure to deliver their SMS message.
    """
    subject = "SMS Delivery Failure Notification"
    body = f"We were unable to deliver your SMS to {to_number}. Please try again later or contact support if the problem persists."
    process_emails(user_id, subject, body)
    logging.info(f"Sent failure notification email to user {user_id}")

def process_sms_replies():
    """
    Processes SMS replies received through the system.
    This function retrieves unprocessed SMS messages from the database and sends
    email replies for each of them.
    """
    unprocessed_sms = get_unprocessed_sms()
    for sms in unprocessed_sms:
        sms_id, contact_id, message, text_id, number = sms
        send_email_reply(contact_id, message, text_id, number)

def send_email_reply(contact_id, message, text_id, number):
    """
    Sends an email reply for an incoming SMS message.
    Parameters:
    - contact_id (int): The ID of the contact who sent the SMS
    - message (str): The content of the SMS message
    - text_id (str): The unique identifier of the SMS
    - number (str): The phone number that sent the SMS

    This function retrieves user information associated with the contact,
    composes an email with the SMS content, and sends it to the user.
    It also updates the SMS as processed if the email is sent successfully.
    """
    user_info = get_user_info_by_contact_id(contact_id)

    if user_info:
        user_id, user_name, contact_name = user_info
        subject = f"SMS from {contact_name}"
        body = f"Message from {contact_name} ({number}):\n\n{message}"

        if process_emails(user_id, subject, body):
            update_sms_processed(text_id)
            logging.info(f"Email reply sent to user {user_id} for SMS from {contact_name}")
        else:
            logging.error(f"Failed to send email reply for SMS {text_id}")
    else:
        logging.error(f"User info not found for contact ID {contact_id}")

def check_quota(api_key):
    """
    Checks the remaining SMS quota for the given API key.
    Parameters:
    - api_key (str): The API key to check the quota for

    Returns:
    - int or None: The remaining quota if successful, None if the check fails

    This function queries the Textbelt API to get the remaining SMS quota
    for the provided API key. It logs the result and handles any errors
    that occur during the process.
    """
    try:
        response = requests.get(SMS_QUOTA_URL.format(api_key))
        result = response.json()
        if result.get('success'):
            quota_remaining = result.get('quotaRemaining')
            logging.info(f"Quota remaining: {quota_remaining}")
            return quota_remaining
        else:
            logging.error("Failed to check quota.")
            return None
    except requests.RequestException as e:
        logging.error(f"Error checking quota: {str(e)}")
        return None

def handle_long_email_reply(user_id, subject, body):
    """
    Handles email replies that exceed the 13000 character limit.
    Parameters:
    - user_id (int): The ID of the user sending the email
    - subject (str): The subject of the email
    - body (str): The body of the email

    This function splits long email bodies into multiple parts if they exceed
    13000 characters. It sends each part as a separate email, adjusting the
    subject line to indicate continuation for parts after the first.
    """
    if len(body) > 13000:
        parts = [body[i:i+13000] for i in range(0, len(body), 13000)]
        for i, part in enumerate(parts):
            if i == 0:
                process_emails(user_id, subject, part)
            else:
                continued_subject = f"{subject} - Cont. ({i+1}/{len(parts)})"
                process_emails(user_id, continued_subject, part)
        logging.info(f"Long email reply split into {len(parts)} parts for user {user_id}")
    else:
        process_emails(user_id, subject, body)

if __name__ == "__main__":
    logging.info("Starting SMS processing")
    process_sms_replies()
    quota = check_quota(API_KEY)
    if quota is not None:
        logging.info(f"Current SMS quota: {quota}")
    logging.info("SMS processing completed")