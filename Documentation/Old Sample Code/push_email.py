## push_email.py ##

import logging
from selectolax.lexbor import LexborHTMLParser
from variables import *
from db_ops import *

def get_unprocessed_sms(cursor):
    """Fetch unprocessed SMS messages from the database."""
    cursor.execute("SELECT SMSID, ContactID, Message, EmailID FROM SMS WHERE Processed = 'N'")
    return cursor.fetchall()

def get_email_details(cursor, email_id):
    """Fetch email details based on EmailID."""
    cursor.execute("SELECT MessageID, UserID FROM Emails WHERE EmailID = ?", (email_id,))
    return cursor.fetchone()

def get_user_name(cursor, user_id):
    """Fetch user's name based on UserID."""
    cursor.execute("SELECT Name FROM Users WHERE UserID = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def send_email_responses(session):
    """
    Process unprocessed SMS messages and send email responses.
    """
    db_connection, cursor = None, None
    try:
        db_connection, cursor = get_database_connection()
        if not db_connection or not cursor:
            logging.error("Failed to establish database connection.")
            return

        # Fetch unprocessed SMS messages
        cursor.execute("SELECT SMSID, ContactID, Message, EmailID FROM SMS WHERE Processed = 'N'")
        unprocessed_sms = cursor.fetchall()
        
        for sms in unprocessed_sms:
            sms_id, contact_id, message_content, email_id = sms
            
            # Fetch email details
            cursor.execute("SELECT MessageID, UserID FROM Emails WHERE EmailID = ?", (email_id,))
            email_details = cursor.fetchone()
            if not email_details:
                logging.error(f"No email found for EmailID: {email_id}")
                continue
            
            message_id, user_id = email_details
            
            # Fetch user details
            cursor.execute("SELECT Name FROM Users WHERE UserID = ?", (user_id,))
            user_result = cursor.fetchone()
            user_name = user_result[0] if user_result else "Unknown User"
            
            reply_url = REPLY_URL_BASE.format(message_id=message_id)
            
            # Use the existing session to make the request
            response = session.get(reply_url)
            response.raise_for_status()

            # Save the HTML content to a file
            # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # filename = f"reply_page_{message_id}_{timestamp}.html"
            # with open(filename, 'w', encoding='utf-8') as f:
            #     f.write(response.text)
            # logging.info(f"Saved reply page HTML to {filename}")

            # Parse the HTML content
            parser = LexborHTMLParser(response.text)

            # Find the textarea for the message body
            textarea = parser.css_first('#ctl00_mainContentPlaceHolder_messageTextBox')
            if not textarea:
                logging.error(f"Textarea not found in the HTML content for MessageID: {message_id}")
                continue

            # Prepare the form data for sending the message
            form_data = {
                'ctl00$mainContentPlaceHolder$messageTextBox': message_content,
                'ctl00$mainContentPlaceHolder$sendMessageButton': 'Send'
            }

            # Add any additional hidden fields that might be necessary
            for hidden_input in parser.css('input[type="hidden"]'):
                name = hidden_input.attrs.get('name')
                value = hidden_input.attrs.get('value', '')
                if name:
                    form_data[name] = value

            # Send the POST request to submit the form
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': reply_url
            }
            response = session.post(reply_url, data=form_data, headers=headers)
            response.raise_for_status()

            # Check if the message was sent successfully
            if "Message sent successfully" in response.text:
                logging.info(f"Email response sent successfully to user: {user_name} (ID: {user_id})")
                
                # Update the database to mark the SMS as processed
                cursor.execute("UPDATE SMS SET Processed = 'Y' WHERE SMSID = ?", (sms_id,))
                db_connection.commit()
                logging.info(f"Database updated: SMS {sms_id} marked as processed.")
            else:
                logging.error(f"Failed to send email response for SMS {sms_id}. Unexpected response content.")
                logging.debug(f"Response content: {response.text[:500]}...")  # Log first 500 characters of response
                
                # # Save the failed response content for debugging
                # error_filename = f"failed_response_{message_id}_{timestamp}.html"
                # with open(error_filename, 'w', encoding='utf-8') as f:
                #     f.write(response.text)
                # logging.info(f"Saved failed response HTML to {error_filename}")

    except Exception as e:
        logging.error(f"An error occurred while processing email responses: {e}")
    finally:
        close_database_resources(db_connection, cursor)

def initialize_and_send_email_responses(session):
    """
    Initialize necessary data and call send_email_responses.
    This function can be called directly from main.py.
    """
    try:
        send_email_responses(session)
    except Exception as e:
        logging.error(f"Error in initialize_and_send_email_responses: {e}")