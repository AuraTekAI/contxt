
from db_ops import fetch_email_details, close_database_resources, \
    fetch_unprocessed_sms, get_database_connection, update_sms_processed_value

import datetime

import logging

def convert_cookies_to_splash_format(splash_cookies=None, cookies=None):
    """
    Converts cookies to the format required by Splash.

    Parameters:
    - splash_cookies (list): The list to which formatted cookies will be appended.
    - cookies (dict): The dictionary of cookies to be converted, with cookie names as keys and cookie values as values.

    Returns:
    - list: The updated list of Splash-formatted cookies if both parameters are provided.
    - bool: False if the necessary parameters are not provided.

    This function takes a dictionary of cookies and appends them to a list in a format that can be used by Splash,
    including setting attributes such as name, value, expiration time, path, httpOnly, secure, and domain.
    If either parameter is missing or None, the function returns False.
    """
    if (not splash_cookies == None) and (cookies):
        now = datetime.datetime.now()
        expires = now + datetime.timedelta(hours=1)
        for name, value in cookies.items():
            cookie = {
                'name': name,
                'value': value,
                'expires': expires.isoformat(),
                'path': '/',
                'httpOnly': True,
                'secure': True,
                'domain': 'www.corrlinks.com'
            }
            splash_cookies.append(cookie)
        return splash_cookies
    else:
        return False
    

def get_sms_replies_for_send_email(message_id_content=None):
    """
    Retrieves unprocessed SMS messages and their corresponding email details, 
    and prepares them for sending email replies.

    Args:
    - message_id_content (list): A list to store SMS ID, Message ID, and Message content. 
      If provided, the function appends the data to this list.

    Returns:
    - list: A list of lists where each inner list contains:
        - sms_id (int): The ID of the unprocessed SMS.
        - message_id (int): The corresponding Message ID from the Emails table.
        - message_content (str): The content of the SMS to be sent as an email reply.
      Returns None if an error occurs.

    Exceptions:
    - Logs an error if the database connection fails or if no email details are found for a given EmailID.
    - Catches and logs any general exceptions that occur during processing.
    
    Example Usage:
    - message_id_content = []
    - message_id_content = get_sms_replies_for_send_email(message_id_content)
    """
    if not message_id_content == None:
        try:
            db_connection, cursor = get_database_connection()
            if not db_connection or not cursor:
                logging.error("Failed to establish database connection.")
                return
            
            message_id_content_temp = []
            # Fetch unprocessed SMS messages
            unprocessed_sms = fetch_unprocessed_sms(cursor)
            for sms in unprocessed_sms:
                sms_id, contact_id, message_content, email_id = sms
                
                # Fetch email details
                email_details = fetch_email_details(cursor, email_id)
                if not email_details:
                    logging.error(f"No email found for EmailID: {email_id}")
                    continue

                message_id, user_id = email_details

                message_id_content_temp = [sms_id, message_id, message_content]
                message_id_content.append(message_id_content_temp)
            
            return message_id_content
                
        except Exception as e:
            print(e)
            logging.error(f"An error occurred while processing email responses: {e}")
        finally:
            close_database_resources(db_connection, cursor)


def update_sms_processed_status(sms_id=None):
    """
    Updates the 'Processed' status of a specific SMS in the database to 'Y' (processed).

    Args:
    - sms_id (int, optional): The ID of the SMS that needs to be marked as processed.

    Returns:
    - bool: True if the SMS status was successfully updated, False otherwise.

    Exceptions:
    - Logs an error if the database connection fails or if the SMS ID is not provided.
    - Rolls back the transaction if an exception occurs during the update operation.
    - Catches and logs any general exceptions that occur during processing.
    
    Example Usage:
    - success = update_sms_processed_status(sms_id=123)
    """
    try:
        db_connection, cursor = get_database_connection()
        if not db_connection or not cursor:
            logging.error("Failed to establish database connection.")
            return
        if not sms_id == None:
            update_sms_processed_value(cursor=cursor, sms_id=sms_id)
            db_connection.commit()
            return True
        else:
            return False
    except Exception as e:
        logging.error(e)
        if db_connection:
            db_connection.rollback()
        return False
    finally:
        close_database_resources(db_connection, cursor)