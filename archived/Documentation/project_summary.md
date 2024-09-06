# push_email.py

```py
# push_email.py

import logging
import requests
import time
import re
import json
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from login import *
from variables import *

# Set up logging
logging.basicConfig(filename='push_email_interaction.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Static cookies (these don't change between sessions)
STATIC_COOKIES = {
    '__cflb': '02DiuJS4Qt1fYJgjizGYDpBdpvG3kZuePiK6aACa2VVk8',
    'cf_clearance': 'NVzVrHA955EqW3BWDz88iyjl3C9DgxYunr5aA39Ime0-1720556066-1.0.1.1-iRuayH1JZaLN0s7CorH6YLiiL6473CYJDarLnx57PclIoO3rJL1j_WVDVTzRamuBzuDeGSzZA8Hf4rj2BVzjZg'
}

def capture_session_state(session):
    """
    Captures the current state of the session, including headers and dynamic cookies.
    Parameters:
    - session (requests.Session): The session object to capture state from

    Returns:
    - dict: A dictionary containing the captured session state

    This function extracts and logs the current headers and cookies from the session,
    excluding static cookies. It's used to preserve session state for later use.
    """
    state = {
        'headers': dict(session.headers),
        'cookies': {k: v for k, v in session.cookies.items() if k not in STATIC_COOKIES}
    }
    logging.info("Captured session state:")
    logging.info(json.dumps(state, indent=2))
    return state

def update_session_state(session, state):
    """
    Updates the session with the captured state.
    Parameters:
    - session (requests.Session): The session object to update
    - state (dict): The state to apply to the session

    This function updates the headers and cookies of the given session object
    with the provided state. It also adds static cookies to ensure all necessary
    session data is present.
    """
    session.headers.update(state['headers'])
    session.cookies.update(state['cookies'])
    session.cookies.update(STATIC_COOKIES)

def log_response_info(response):
    """
    Logs detailed information about an HTTP response.
    Parameters:
    - response (requests.Response): The response object to log

    This function logs various details of the HTTP response including URL,
    status code, headers, cookies, and a portion of the response body.
    It also saves the full HTML content to a file for inspection.
    """
    logging.info(f"=== RESPONSE INFO ===")
    logging.info(f"URL: {response.url}")
    logging.info(f"Status Code: {response.status_code}")
    logging.info(f"Headers: {json.dumps(dict(response.headers), indent=2)}")
    logging.info(f"Cookies: {json.dumps(dict(response.cookies), indent=2)}")
    logging.info(f"Response Body: {response.text[:1000]}")
    logging.info(f"=====================")

    # Save the full HTML content to a file for inspection
    with open(f"response_content_{response.status_code}.html", "w", encoding="utf-8") as f:
        f.write(response.text)

def send_email_reply(session, form_data, message_content, message_id, session_state):
    """
    Sends an email reply through the Corrlinks system.
    Parameters:
    - session (requests.Session): The session object for making requests
    - form_data (dict): The form data extracted from the reply page
    - message_content (str): The content of the reply message
    - message_id (str): The ID of the message being replied to
    - session_state (dict): The current state of the session

    Returns:
    - bool: True if the email was sent successfully, False otherwise

    This function handles the entire process of sending an email reply,
    including navigating to the reply page, submitting the form with the
    reply content, and handling any redirects or confirmations.
    """
    reply_url = f"https://www.corrlinks.com/NewMessage.aspx?messageId={message_id}&type=reply"
    
    # Step 1: GET request to the reply page
    headers = session_state['headers'].copy()
    headers['Referer'] = 'https://www.corrlinks.com/Inbox.aspx'
    response = session.get(reply_url, headers=headers)
    log_response_info(response)

    if response.status_code != 200:
        logging.error(f"Failed to load reply page. Status code: {response.status_code}")
        return False

    # Extract all form fields, including hidden ones
    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form', {'id': 'aspnetForm'})
    all_form_data = {}
    for input_tag in form.find_all(['input', 'textarea']):
        name = input_tag.get('name')
        value = input_tag.get('value', '')
        if name:
            all_form_data[name] = value

    # Update with our message content and other necessary fields
    all_form_data.update({
        'ctl00$mainContentPlaceHolder$messageTextBox': message_content,
        'ctl00$mainContentPlaceHolder$sendMessageButton': 'Send'
    })

    # Prepare headers for POST request
    headers = session_state['headers'].copy()
    if 'content-type' in headers:
        del headers['content-type']
    headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': reply_url
    })

    # Remove any headers with empty or None values
    headers = {k: v for k, v in headers.items() if v}
    
    # Ensure all header names and values are strings
    headers = {str(k).strip(): str(v).strip() for k, v in headers.items()}

    logging.info("Headers being sent:")
    logging.info(json.dumps(headers, indent=2))

    logging.info("Data being sent:")
    logging.info(json.dumps(all_form_data, indent=2))

    # Send POST request
    response = session.post(reply_url, data=all_form_data, headers=headers)
    log_response_info(response)
    
    # After the POST request
    js_redirect = re.search(r"window.location.href\s*=\s*['\"](.+?)['\"]", response.text)
    if js_redirect:
        redirect_url = js_redirect.group(1)
        logging.info(f"JavaScript redirect found to: {redirect_url}")
        # Follow the JavaScript redirect
        response = session.get(urljoin(reply_url, redirect_url), headers=headers)
        log_response_info(response)
        logging.info(f"Final URL after POST: {response.url}")
        logging.info(f"Response headers: {dict(response.headers)}")

    if response.status_code == 200:
        # Check for AJAX response indicating success
        if 'pageRedirect' in response.text and 'MessageProcessed.aspx?type=send' in response.text:
            logging.info("Email sent successfully. Redirecting to MessageProcessed page.")
            
            # Extract the redirect URL from the AJAX response
            redirect_url = re.search(r'\'(/MessageProcessed\.aspx\?type=send[^\']+)\'', response.text)
            if redirect_url:
                processed_url = urljoin(reply_url, redirect_url.group(1))
                headers = session_state['headers'].copy()
                headers['Referer'] = reply_url
                processed_response = session.get(processed_url, headers=headers)
                log_response_info(processed_response)
                
                if 'Message successfully sent.' in processed_response.text:
                    logging.info("Confirmed successful send on MessageProcessed page.")
                    return True
                else:
                    logging.error("MessageProcessed page doesn't contain expected confirmation.")
                    return False
            else:
                logging.error("Couldn't extract redirect URL from AJAX response.")
                return False
        else:
            logging.error("Unexpected response content.")
            logging.debug(f"Response content: {response.text[:1000]}")
            return False
    else:
        logging.error(f"Unexpected response status code: {response.status_code}")
        return False

def navigate_to_reply_page(session, message_id):
    """
    Navigates to the reply page for a specific message.
    Parameters:
    - session (requests.Session): The session object for making requests
    - message_id (str): The ID of the message to reply to

    Returns:
    - tuple: (response, form_data) where response is the HTTP response and
             form_data is the extracted form data from the reply page

    This function sends a GET request to the reply page for a specific message
    and extracts the form data needed for submitting a reply.
    """
    reply_url = REPLY_URL_BASE.format(message_id=message_id)
    logging.info(f"Navigating to Reply page: {reply_url}")
    response = session.get(reply_url)
    log_response_info(response)
    
    form_data = extract_form_data(response.text)
    
    return response, form_data

def extract_form_data(html):
    """
    Extracts form data from an HTML page.
    Parameters:
    - html (str): The HTML content of the page

    Returns:
    - dict: A dictionary containing the extracted form field names and values

    This function uses BeautifulSoup to parse the HTML and extract all input,
    select, and textarea fields from the form. It's used to prepare data for
    form submissions.
    """
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find('form', id='aspnetForm')
    if not form:
        logging.warning("Form not found in HTML")
        return {}
    
    form_data = {}
    for input_tag in form.find_all(['input', 'select', 'textarea']):
        name = input_tag.get('name')
        value = input_tag.get('value', '')
        if name:
            form_data[name] = value
    
    logging.info("Extracted Form Data:")
    logging.info(json.dumps(form_data, indent=2))
    return form_data

def run_push_email():
    """
    Runs the push email process.
    Returns:
    - str: A message indicating the result of the process

    This function orchestrates the process of sending a test reply email.
    It logs into Corrlinks, navigates to the reply page, sends the email reply,
    and handles the response. It's designed for testing and logging purposes.
    """
    message_id = "3706018280"
    message_content = "This is a test reply message."
    
    session = login_to_corrlinks()
    if not session:
        logging.error("Failed to login to Corrlinks")
        return "Failed to login to Corrlinks"

    # Capture the session state right after login
    session_state = capture_session_state(session)

    response, form_data = navigate_to_reply_page(session, message_id)
    if response.status_code != 200:
        logging.error(f"Failed to navigate to Reply page. Status code: {response.status_code}")
        # Save the HTML content to a file
        filename = f"reply_page_{message_id}-Reply-Page.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        logging.info(f"Saved reply page HTML to {filename}")
        return f"Failed to navigate to Reply page. Status code: {response.status_code}"

    time.sleep(1)  # 1 second delay

    success = send_email_reply(session, form_data, message_content, message_id, session_state)
    if success:
        logging.info("Email reply sent successfully")
        # Save the HTML content to a file
        filename = f"reply_page_{message_id}-Success.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        logging.info(f"Saved reply page HTML to {filename}")
        return "Email reply sent successfully. Check push_email_interaction.log for details."
    else:
        logging.error("Failed to send email reply")
        # Save the HTML content to a file
        filename = f"reply_page_{message_id}-Failed.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        logging.info(f"Saved reply page HTML to {filename}")
        return "Failed to send email reply. Check push_email_interaction.log for details."

if __name__ == "__main__":
    print(run_push_email())
```

# db_ops.py

```py
## db_ops.py ##

import pyodbc
import logging
import re
from typing import List, Dict
from datetime import datetime, timedelta
from variables import *
from push_email import process_emails

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variable to store the email callback
email_callback = None

def set_email_callback(callback):
    """
    Sets the email callback function.
    Parameters:
    - callback (function): The function to be used as the email callback.

    This function assigns the provided callback function to a global variable, allowing it to be used for email processing throughout the program.
    """
    global email_callback
    email_callback = callback

def get_database_connection():
    """
    Attempts to establish a database connection using the configuration.
    Returns:
    - connection (pyodbc.Connection): The database connection object.
    - cursor (pyodbc.Cursor): The cursor object for executing SQL commands.

    This function tries to connect to the database, performs a quick test to ensure the connection is active, and returns the connection and cursor objects.
    It includes error handling and logging for connection failures.
    """
    logging.info("Attempting to establish database connection.")
    connection, cursor = None, None
    try:
        connection = pyodbc.connect(DB_SETTINGS['CONN_STR'])
        cursor = connection.cursor()
        # Perform a quick test to ensure the connection is active
        if not check_connection(cursor):
            logging.info("Connection test failed. Trying to reconnect.")
            connection.close()
            connection = pyodbc.connect(DB_SETTINGS['CONN_STR'])
            cursor = connection.cursor()
        logging.info("Database connected successfully.")
    except pyodbc.Error as e:
        logging.error(f"Failed to connect to the database: {e}")
        if connection:
            connection.close()
        return None, None
    return connection, cursor

def check_connection(cursor):
    """
    Tests the given database cursor by attempting to fetch a simple query.
    Parameters:
    - cursor (pyodbc.Cursor): The cursor to test.

    Returns:
    - bool: True if the query succeeds, otherwise False.

    This function is used to verify that a database connection is still active by executing a simple SELECT query.
    """
    try:
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return True
    except pyodbc.Error:
        logging.warning("Database connection appears to be inactive.")
        return False

def close_database_resources(db_connection, cursor):
    """
    Properly closes the database resources.
    Parameters:
    - db_connection (pyodbc.Connection): The database connection to close.
    - cursor (pyodbc.Cursor): The cursor to close.

    This function safely closes both the cursor and the database connection, ensuring that database resources are properly released after use.
    """
    try:
        if cursor is not None:
            cursor.close()
            logging.info("Cursor closed successfully.")
        if db_connection is not None:
            db_connection.close()
            logging.info("Database connection closed successfully.")
    except Exception as e:
        logging.error(f"Failed to close database resources properly: {e}")
        
def save_emails(emails, connection, cursor):
    """
    Saves a batch of emails to the database, including their message IDs.
    Parameters:
    - emails (list): A list of dictionaries containing email data.
    - connection (pyodbc.Connection): The database connection.
    - cursor (pyodbc.Cursor): The cursor for executing SQL commands.

    This function iterates through the provided list of emails and inserts each one into the Emails table in the database.
    It handles commits and rollbacks in case of success or failure.
    """
    if cursor is None or connection is None:
        print("Database connection or cursor is not available.")
        return

    try:
        for email in emails:
            cursor.execute("""
                INSERT INTO Emails (UserID, SentDateTime, Subject, Body, MessageID)
                VALUES (?, ?, ?, ?, ?)
            """, (email['user_id'], email['sent_datetime'], email['subject'], email['body'], email['message_id']))
        connection.commit()
        print("All emails saved successfully.")
    except Exception as e:
        print(f"Failed to save emails: {e}")
        if connection:
            connection.rollback()

def ensure_user_exists(connection, cursor, user_name_id):
    """
    Ensures that a user exists in the database; adds the user if not present.
    Parameters:
    - connection (pyodbc.Connection): The database connection.
    - cursor (pyodbc.Cursor): The cursor for executing SQL commands.
    - user_name_id (str): A string containing the user's name and ID.

    Returns:
    - str: The user ID if successful, None otherwise.

    This function checks if a user exists in the database based on their ID. If not, it adds the user to the database.
    It handles the parsing of the user_name_id string to extract the name and ID.
    """
    try:
        name, user_id = user_name_id.rsplit(' (', 1)
        user_id = user_id.strip(')')
        name = name.strip()
    except ValueError:
        logging.error(f"Invalid format for user_name_id: {user_name_id}")
        return None

    cursor.execute("SELECT UserID FROM Users WHERE UserID = ?", (user_id,))
    result = cursor.fetchone()
    if not result:
        cursor.execute("INSERT INTO Users (UserID, Name, Active) VALUES (?, ?, ?)", (user_id, name, 'N'))
        connection.commit()
        print(f"Added new user: {name} with ID {user_id}")
    else:
        print(f"User already exists: {name} with ID {user_id}")

    return user_id

def save_contact_details(contact_name, phone, email, cursor):
    """
    Saves the contact details into the Contacts table.
    Parameters:
    - contact_name (str): The name of the contact.
    - phone (str, optional): The phone number of the contact.
    - email (str, optional): The email address of the contact.
    - cursor (pyodbc.Cursor): The cursor to execute the SQL command.

    This function dynamically constructs an SQL INSERT query based on the provided contact details and executes it to save the contact information in the database.
    It handles cases where phone or email might be missing.
    """
    try:
        if cursor is not None:
            # Construct the SQL query dynamically based on provided values
            fields = []
            values = []
            params = []

            if contact_name:
                fields.append("ContactName")
                values.append("?")
                params.append(contact_name)
            if phone:
                fields.append("PhoneNumber")
                values.append("?")
                params.append(phone)
            if email:
                fields.append("EmailAddress")
                values.append("?")
                params.append(email)

            sql = f"INSERT INTO Contacts ({', '.join(fields)}) VALUES ({', '.join(values)})"
            cursor.execute(sql, tuple(params))
            cursor.commit()
            logging.info(f"Saved contact details for {contact_name}")
        else:
            logging.warning("Database cursor is not available.")
    except Exception as e:
        logging.error(f"Failed to save contact details: {e}")

def check_user_active(full_name):
    """
    Checks if a user is active in the database.
    Parameters:
    - full_name (str): The full name of the user to check.

    Returns:
    - bool: True if the user is active, False otherwise.

    This function queries the database to check the 'Active' status of a user based on their full name.
    It returns True if the user is found and their status is 'Y', False otherwise.
    """
    conn_str = DB_SETTINGS['CONN_STR']
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT Active FROM users WHERE Name = ?", full_name)
    row = cursor.fetchone()
    conn.close()
    if row:
        return row.Active == 'Y'
    return False
    
def update_user_info(user_info):
    """
    Updates user information in the database.
    Parameters:
    - user_info (dict): A dictionary containing user information to update.

    This function constructs an UPDATE SQL query using the provided user information and executes it to update the user's details in the database.
    It handles commits and rollbacks for successful updates or errors.
    """
    conn_str = DB_SETTINGS['CONN_STR']
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    try:
        sql = """
        UPDATE users
        SET UserName = ?, Age = ?, Sex = ?, PrivateMode = ?
        WHERE UserID = ?
        """
        params = (user_info['UserName'], user_info['Age'], user_info['Sex'], user_info['PrivateMode'], user_info['UserID'])
        cursor.execute(sql, params)
        conn.commit()
        logging.info(f"User info updated for UserID {user_info['UserID']}")
    except Exception as e:
        logging.error(f"Failed to update user info: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        
def log_sms_to_db(contact_id, message, status, text_id, number, direction):
    """
    Logs an SMS message to the database.
    Parameters:
    - contact_id (int): The ID of the contact associated with the SMS.
    - message (str): The content of the SMS message.
    - status (str): The status of the SMS (e.g., 'Sent', 'Failed').
    - text_id (str): A unique identifier for the SMS.
    - number (str): The phone number the SMS was sent to or received from.
    - direction (str): The direction of the SMS ('Inbound' or 'Outbound').

    This function inserts a new record into the SMS table with the provided information.
    It handles database connection, insertion, and proper resource cleanup.
    """
    connection, cursor = get_database_connection()
    if cursor is None or connection is None:
        logging.error("Database connection or cursor is not available.")
        return
    try:
        # Use 0 as the default ContactID if no valid contact was found
        contact_id = contact_id if contact_id is not None else 12
        
        # Log the data being attempted to save
        logging.info(f"Attempting to save SMS data: ContactID={contact_id}, Message='{message}', Status='{status}', TextID='{text_id}', Number='{number}', Direction='{direction}'")
        
        cursor.execute('''
            INSERT INTO dbo.SMS (ContactID, Message, Status, DateTime, TextID, Number, Direction)
            VALUES (?, ?, ?, GETDATE(), ?, ?, ?)
        ''', (contact_id, message, status, text_id, number, direction))
        connection.commit()
        logging.info("SMS log inserted successfully.")
    except Exception as e:
        logging.error(f"Failed to log SMS to database: {e}")
        logging.error(f"Attempted data: ContactID={contact_id}, Message='{message}', Status='{status}', TextID='{text_id}', Number='{number}', Direction='{direction}'")
        if connection:
            connection.rollback()
    finally:
        close_database_resources(connection, cursor)

# Example usage:
# log_sms_to_db(contact_id=3, message="Test message", status="Sent", text_id="123456789012345", number="1234567890", direction="Outbound")

def update_sms_status_in_db(text_id, status):
    """
    Updates the status of an SMS message in the database.
    Parameters:
    - text_id (str): The unique identifier of the SMS to update.
    - status (str): The new status to set for the SMS.

    This function updates the status of a specific SMS message in the database based on its text_id.
    It handles database connection, update execution, and proper resource cleanup.
    """
    connection, cursor = get_database_connection()
    if cursor is None or connection is None:
        logging.error("Database connection or cursor is not available.")
        return

    try:
        cursor.execute('''
            UPDATE dbo.SMS
            SET Status = ?
            WHERE TextID = ?
        ''', (status, text_id))

        connection.commit()
        logging.info(f"SMS status updated to {status} for Text ID: {text_id}")
    except Exception as e:
        logging.error(f"Failed to update SMS status in database: {e}")
        if connection:
            connection.rollback()
    finally:
        close_database_resources(connection, cursor)

def get_unprocessed_sms():
    """
    Retrieves unprocessed SMS messages from the database.
    Returns:
    - list: A list of tuples containing information about unprocessed SMS messages.

    This function queries the database for SMS messages that are inbound and not yet processed.
    It returns the SMSID, ContactID, Message, TextID, and Number for each unprocessed SMS.
    The function handles database connection and resource cleanup.
    """
    connection, cursor = get_database_connection()
    if not connection or not cursor:
        logging.error("Failed to connect to database")
        return []

    try:
        cursor.execute("""
            SELECT SMSID, ContactID, Message, TextID, Number
            FROM SMS
            WHERE Direction = 'Inbound' AND Processed = 'N'
        """)
        return cursor.fetchall()
    finally:
        close_database_resources(connection, cursor)

def update_sms_processed(text_id):
    """
    Updates the processed status of an SMS message in the database.
    Parameters:
    - text_id (str): The unique identifier of the SMS to update.

    This function marks a specific SMS message as processed in the database.
    It updates the 'Processed' field to 'Y' for the SMS with the given text_id.
    The function handles database connection, update execution, and error logging.
    """
    connection, cursor = get_database_connection()
    if not connection or not cursor:
        logging.error("Failed to connect to database")
        return

    try:
        cursor.execute("UPDATE SMS SET Processed = 'Y' WHERE TextID = ?", (text_id,))
        connection.commit()
        logging.info(f"Updated SMS {text_id} to Processed = 'Y'")
    except Exception as e:
        logging.error(f"Error updating SMS status: {str(e)}")
        connection.rollback()
    finally:
        close_database_resources(connection, cursor)

def get_user_info_by_contact_id(contact_id):
    """
    Retrieves user information based on a contact ID.
    Parameters:
    - contact_id (int): The ID of the contact to look up.

    Returns:
    - tuple: A tuple containing UserID, Name, and ContactName if found, None otherwise.

    This function queries the database to fetch user information associated with a given contact ID.
    It joins the Users and Contacts tables to retrieve the necessary information.
    The function handles database connection and resource cleanup.
    """
    connection, cursor = get_database_connection()
    if not connection or not cursor:
        logging.error("Failed to establish database connection")
        return None

    try:
        cursor.execute("""
            SELECT u.UserID, u.Name, c.ContactName
            FROM Users u
            JOIN Contacts c ON u.UserID = c.UserID
            WHERE c.ContactID = ?
        """, (contact_id,))
        return cursor.fetchone()
    finally:
        close_database_resources(connection, cursor)
        
def parse_contact_emails(driver, db_connection, cursor):
    """
    Fetches and parses contact emails to extract contact information.
    Parameters:
    - driver: The web driver object (likely for web scraping)
    - db_connection: The database connection object
    - cursor: The database cursor object

    This function retrieves emails from the database, processes them to extract contact information,
    and handles various types of contact-related emails (e.g., contact list requests, contact removal).
    It interacts with other functions to update the database and send responses as needed.
    """
    logging.info("Starting to fetch and parse contact emails.")
    try:
        if TEST_MODE:
            query = "SELECT EmailID, UserID, Subject, Body FROM Emails"
        else:
            four_hours_ago = datetime.now() - timedelta(hours=4)
            query = f"""
            SELECT EmailID, UserID, Subject, Body FROM Emails
            WHERE SentDateTime >= '{four_hours_ago.strftime('%Y-%m-%d %H:%M:%S')}'
            """
        
        cursor.execute(query)
        emails = cursor.fetchall()
        logging.debug(f"Fetched {len(emails)} emails to process.")

        for email_id, user_id, subject, body in emails:
            logging.info(f"Processing email ID {email_id} for user ID {user_id} with subject '{subject}'.")
            if subject.lower() == 'contact list':
                send_contact_list_email(user_id, db_connection, driver, cursor)
            elif subject.lower() == 'contact remove':
                contact_name = body.strip()
                remove_contact_from_db(contact_name, db_connection, user_id, driver, cursor)
            elif subject.lower() == 'add contact email':
                add_contact_email(body, db_connection, user_id, driver, cursor)
            elif subject.lower() == 'add contact number':
                add_contact_number(body, db_connection, user_id, driver, cursor)
            elif subject.lower() == 'screen name set':
                set_screen_name(body, db_connection, user_id, driver, cursor)
            elif subject.lower() == 'private':
                set_private_mode(user_id, db_connection, driver, cursor)
            else:
                contact_details = parse_contact_info(body)
                logging.debug(f"Found {len(contact_details)} potential contacts in email ID {email_id}.")
                if contact_details:
                    insert_contacts_to_db(contact_details, db_connection, user_id)
                else:
                    logging.info("No contacts found in this email.")

        db_connection.commit()
        logging.info("All contact details processed and saved successfully.")
    except Exception as e:
        logging.error(f"An error occurred while processing contact emails: {str(e)}")
        if db_connection:
            db_connection.rollback()
    finally:
        # Ensures resources are always cleaned up properly
        if cursor:
            cursor.close()
        if db_connection:
            db_connection.close()
        logging.info("Database connection and cursor closed successfully.")

def parse_contact_info(email_body: str) -> List[Dict]:
    """
    Parses the email body to extract contact information using refined regex.
    Parameters:
    - email_body (str): The body of the email to parse

    Returns:
    - list: A list of dictionaries containing extracted contact information

    This function uses regular expressions to extract contact details like names, phone numbers,
    email addresses, and usernames from the email body. It handles various formats and combinations
    of contact information.
    """
    logging.info("Parsing contact information from email body.")
    pattern = re.compile(
        r"([\w\s]+?)(Ph#\s*(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})|Email\s*([\w\.\-]+@[\w\.\-]+\.\w{2,})|UN#\s*([\w]+))(?=\s+[\w\s]*?Ph#|\s+[\w\s]*?Email|\s+[\w\s]*?UN#|$)"
    )

    contacts = []
    matches = pattern.finditer(email_body)
    current_contact = {}

    for match in matches:
        # Extract information
        name = match.group(1).strip()
        phone = match.group(3) if match.group(3) else None
        email = match.group(4) if match.group(4) else None
        username = match.group(5) if match.group(5) else None

        if name and (not current_contact or name != current_contact.get('ContactName')):
            if current_contact and current_contact not in contacts:
                contacts.append(current_contact)
            current_contact = {
                'ContactName': name,
                'PhoneNumber': phone,
                'EmailAddress': email,
                'UserName': username
            }
        else:
            if phone:
                current_contact['PhoneNumber'] = phone
            if email:
                current_contact['EmailAddress'] = email
            if username:
                current_contact['UserName'] = username

    if current_contact and current_contact not in contacts:
        contacts.append(current_contact)

    logging.debug(f"Extracted {len(contacts)} contacts from the email.")
    return contacts

def get_contact_by_phone(db_connection, user_id: int, phone_number: str) -> Dict:
    """
    Looks up a contact based on the phone number for a specific user.
    Parameters:
    - db_connection: The database connection object
    - user_id (int): The ID of the user
    - phone_number (str): The phone number to look up

    Returns:
    - dict: A dictionary containing the contact information, or None if not found

    This function normalizes the given phone number and searches for a matching contact in the database.
    It returns contact details including ContactID, ContactName, PhoneNumber, and EmailAddress.
    The function handles phone number normalization and database querying.
    """
    cursor = db_connection.cursor()
    try:
        # Normalize the phone number by removing non-digit characters
        normalized_phone = ''.join(filter(str.isdigit, phone_number))
        
        query = """
        SELECT ContactID, ContactName, PhoneNumber, EmailAddress
        FROM Contacts
        WHERE UserID = ? AND REPLACE(REPLACE(REPLACE(PhoneNumber, '-', ''), '.', ''), ' ', '') = ?
        """
        cursor.execute(query, (user_id, normalized_phone))
        result = cursor.fetchone()
        
        if result:
            return {
                'ContactID': result[0],
                'ContactName': result[1],
                'PhoneNumber': result[2],
                'EmailAddress': result[3]
            }
        else:
            return None
    except Exception as e:
        logging.error(f"Error looking up contact by phone number: {str(e)}")
        return None
    finally:
        cursor.close()

def insert_contacts_to_db(contacts: List[Dict], db_connection, user_id: int, driver, cursor):
    """
    Inserts the contact information into the database after checking for duplicates.
    Parameters:
    - contacts (List[Dict]): A list of dictionaries containing contact information
    - db_connection: The database connection object
    - user_id (int): The ID of the user associated with these contacts
    - driver: The web driver object (likely for web scraping)
    - cursor: The database cursor object

    This function checks for duplicate contacts, inserts new contacts into the database,
    and handles sending reply emails for duplicate contacts. It also logs the operations.
    """
    cursor = db_connection.cursor()
    reply_contacts = []
    for contact in contacts:
        logging.debug(f"Preparing to insert or check duplicate for contact: {contact}")
        sql_check = "SELECT ContactName FROM Contacts WHERE UserID = ? AND ContactName = ?"
        cursor.execute(sql_check, (user_id, contact['ContactName']))
        if cursor.fetchone():
            logging.error(f"Duplicate contact name found for UserID {user_id}: {contact['ContactName']}")
            reply_contacts.append(contact['ContactName'])
        else:
            sql_insert = """
            INSERT INTO Contacts (UserID, ContactName, PhoneNumber, EmailAddress, UserName)
            VALUES (?, ?, ?, ?, ?)
            """
            params = (user_id, contact['ContactName'], contact.get('PhoneNumber', None), 
                      contact.get('EmailAddress', None), contact.get('UserName', None))
            logging.debug(f"Executing insert with params: {params}")
            cursor.execute(sql_insert, params)
            db_connection.commit()
            logging.info(f"Inserted contact {contact['ContactName']} for user ID {user_id}.")

    if reply_contacts:
        message_content = f"Error: Duplicate contact names found: {', '.join(reply_contacts)}. Consider using last initials."
        process_emails(driver, db_connection, cursor, user_id, message_content)

def send_contact_list_email(user_id, db_connection, cursor):
    """
    Sends an email containing the user's current contact list.
    Parameters:
    - user_id (int): The ID of the user requesting their contact list
    - db_connection: The database connection object
    - cursor: The database cursor object

    This function retrieves the user's contacts from the database, formats them into a list,
    and sends an email to the user with their contact list. It uses the email_callback function
    to send the email.
    """
    cursor.execute("SELECT ContactName, PhoneNumber, EmailAddress FROM Contacts WHERE UserID = ?", (user_id,))
    contacts = cursor.fetchall()
    contact_list = "\n".join([f"{name} - {phone} - {email}" for name, phone, email in contacts])
    message_content = f"Your current contact list:\n{contact_list}"
    logging.info(f"Drafting contact list email for user {user_id}: {message_content}")
    if email_callback:
        email_callback(user_id, "Your Contact List", message_content)
    else:
        logging.error("Email callback not set. Unable to send contact list email.")

def remove_contact_from_db(contact_name, db_connection, user_id, cursor):
    """
    Removes a contact from the database.
    Parameters:
    - contact_name (str): The name of the contact to remove
    - db_connection: The database connection object
    - user_id (int): The ID of the user who owns the contact
    - cursor: The database cursor object

    This function deletes a specified contact from the database for a given user.
    It also sends a confirmation email to the user about the contact removal.
    """
    cursor.execute("DELETE FROM Contacts WHERE UserID = ? AND ContactName = ?", (user_id, contact_name))
    db_connection.commit()
    logging.info(f"Removed contact {contact_name} for user ID {user_id}.")
    message_content = f"The contact '{contact_name}' has been removed from your contact list."
    if email_callback:
        email_callback(user_id, "Contact Removed", message_content)
    else:
        logging.error("Email callback not set. Unable to send contact removal confirmation.")

def add_contact_email(email_body, db_connection, user_id, driver, cursor):
    """
    Adds a contact email to the database.
    Parameters:
    - email_body (str): The body of the email containing contact information
    - db_connection: The database connection object
    - user_id (int): The ID of the user adding the contact
    - driver: The web driver object (likely for web scraping)
    - cursor: The database cursor object

    This function parses the email body to extract a contact name and email address,
    then adds this information to the database. It also sends an updated contact list to the user.
    """
    lines = email_body.splitlines()
    if len(lines) >= 2:
        contact_name = lines[0].strip()
        email = lines[1].strip()
        contact = {'ContactName': contact_name, 'EmailAddress': email}
        insert_contacts_to_db([contact], db_connection, user_id)
        send_contact_list_email(user_id, db_connection, driver, cursor)

def add_contact_number(email_body, db_connection, user_id, driver, cursor):
    """
    Adds a contact number to the database.
    Parameters:
    - email_body (str): The body of the email containing contact information
    - db_connection: The database connection object
    - user_id (int): The ID of the user adding the contact
    - driver: The web driver object (likely for web scraping)
    - cursor: The database cursor object

    This function parses the email body to extract a contact name and phone number,
    then adds this information to the database. It also sends an updated contact list to the user.
    """
    lines = email_body.splitlines()
    if len(lines) >= 2:
        contact_name = lines[0].strip()
        phone = lines[1].strip()
        contact = {'ContactName': contact_name, 'PhoneNumber': phone}
        insert_contacts_to_db([contact], db_connection, user_id)
        send_contact_list_email(user_id, db_connection, driver, cursor)

def set_screen_name(body, db_connection, user_id, cursor):
    """
    Sets the screen name for the user.
    Parameters:
    - body (str): The body of the email containing the new screen name
    - db_connection: The database connection object
    - user_id (int): The ID of the user updating their screen name
    - cursor: The database cursor object

    This function updates the user's screen name in the database and sends a confirmation email to the user.
    """
    cursor.execute("UPDATE Users SET ScreenName = ? WHERE UserID = ?", (body.strip(), user_id))
    db_connection.commit()
    logging.info(f"Screen name set to {body.strip()} for user ID {user_id}.")
    message_content = f"Your screen name has been set to {body.strip()}."
    if email_callback:
        email_callback(user_id, "Screen Name Updated", message_content)
    else:
        logging.error("Email callback not set. Unable to send screen name update confirmation.")

def set_private_mode(user_id, db_connection, cursor):
    """
    Sets the user to private mode.
    Parameters:
    - user_id (int): The ID of the user to set to private mode
    - db_connection: The database connection object
    - cursor: The database cursor object

    This function updates the user's privacy setting in the database to 'Y' (private)
    and sends a confirmation email to the user about the change.
    """
    cursor.execute("UPDATE Users SET PrivateMode = 'Y' WHERE UserID = ?", (user_id,))
    db_connection.commit()
    logging.info(f"User ID {user_id} set to private mode.")
    message_content = "Your account has been set to private mode."
    if email_callback:
        email_callback(user_id, "Private Mode Activated", message_content)
    else:
        logging.error("Email callback not set. Unable to send private mode activation confirmation.")

```

# main.py

```py
## main.py ##

import logging
import schedule
import time
import tkinter as tk
import threading
from tkinter import messagebox
from datetime import datetime, timedelta
from accept_invite import *
from pull_email import *
from db_ops import *
from send_sms import *
from variables import *
from push_email import *
from login import *

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_email_callback():
    """
    Sets up the email callback for db_ops.
    This function initializes the email callback by calling set_email_callback with process_emails as the argument.
    It's expected to be called at the start of the program to ensure email processing is properly configured.
    """
    set_email_callback(process_emails)

def setup_interactive_window():
    """
    Sets up the interactive window for test mode actions.
    This function creates a tkinter window with various buttons for different actions like email retrieval, SMS sending, and invitation processing.
    It's used in test mode to allow manual triggering of different functionalities for debugging and testing purposes.
    """
    window = tk.Tk()
    window.title("Debug Mode")

    # Get the screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Calculate the window dimensions and position
    window_width = 250
    window_height = 230
    window_x = (screen_width // 2) - (window_width // 2)
    window_y = (screen_height // 2) - (window_height // 2)

    # Set the window geometry and position
    window.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")

    # Add padding (border) around the window content
    window.configure(padx=10, pady=10)

    def handle_email_retrieval():
        """
        Handles the email retrieval process.
        This function is called when the "Retrieve Emails" button is clicked in the interactive window.
        It initializes the environment and executes the process_unread_emails function to fetch and process new emails.
        """
        initialize_and_execute(process_unread_emails)

    def send_email_responses_threaded():
        """
        Sends email responses in a separate thread.
        This function creates a new thread to run the process_emails function, which handles sending email responses.
        It's designed to prevent the GUI from freezing during the email sending process and provides feedback via message boxes.
        """
        def thread_function():
            try:
                process_emails()  # This is the function from push_email_gui.py
                messagebox.showinfo("Success", "Email process completed.")
            except Exception as e:
                logging.error(f"An error occurred: {str(e)}")
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        threading.Thread(target=thread_function).start()

    def parse_contact_emails_threaded():
        """
        Parses contact emails in a separate thread.
        This function creates a new thread to run the parse_contact_emails function, which processes emails to extract contact information.
        It's designed to prevent the GUI from freezing during the parsing process.
        """
        threading.Thread(target=lambda: initialize_and_execute(parse_contact_emails)).start()

    def accept_invite():
        """
        Handles the invitation acceptance process.
        This function fetches an invite code and user name from an email, then processes the invitation using this information.
        It runs in a separate thread and provides feedback via message boxes about the success or failure of the invitation acceptance.
        """
        def thread_function():
            # Fetch invite code from email
            invite_code, email_id, full_name = fetch_invite_code_and_name()
        
            if invite_code and full_name:
                print(f"Invite Code: {invite_code}")
                print(f"User Name: {full_name}")
                # Process invitation using the invite code and email ID
                result = process_invitation()
                if result:
                    messagebox.showinfo("Invitation Accepted", f"Successfully accepted invitation for {full_name}")
                else:
                    messagebox.showerror("Invitation Failed", f"Failed to accept invitation for {full_name}")
            else:
                messagebox.showinfo("No Invite", "No invite code found.")
    
        threading.Thread(target=thread_function).start()

    def run_push_email():
        """
        Runs the data logger push email process in a separate thread.
        This function executes the run_push_email function in a new thread and displays the result in a message box.
        It's used for logging and pushing email data, likely for debugging or monitoring purposes.
        """
        def thread_function():
            result = run_push_email()
            messagebox.showinfo("Data Logger Result", result)
        threading.Thread(target=thread_function).start()

    # Define button actions
    tk.Button(window, text="Retrieve Emails", command=handle_email_retrieval).pack(fill=tk.X)
    tk.Button(window, text="Send SMS", command=send_sms_threaded).pack(fill=tk.X)
    tk.Button(window, text="Reply to Emails", command=send_email_responses_threaded).pack(fill=tk.X)
    tk.Button(window, text="Parse Contact Emails", command=parse_contact_emails_threaded).pack(fill=tk.X)
    tk.Button(window, text="Accept Invite", command=accept_invite).pack(fill=tk.X)
    tk.Button(window, text="Data Logger", command=run_push_email).pack(fill=tk.X)
    tk.Button(window, text="Reply to CorrLinks P2P", command=lambda: messagebox.showinfo("Placeholder", "P2P functionality")).pack(fill=tk.X)
    tk.Button(window, text="Answer ChatGPT Questions", command=lambda: messagebox.showinfo("Placeholder", "ChatGPT functionality")).pack(fill=tk.X)

    window.mainloop()

def initialize_and_execute(task_function):
    """
    Initializes the environment and executes a given task function.
    Parameters:
    - task_function (function): The function to be executed after initialization.

    This function logs into Corrlinks, establishes a database connection, executes the provided task function, and ensures proper cleanup of resources afterwards.
    It's a general-purpose function used to set up the necessary environment for various operations.
    """
    session = login_to_corrlinks()
    if not session:
        logging.error("Failed to initialize the session.")
        return
    db_connection, cursor = get_database_connection()

    try:
        if db_connection and cursor:
            task_function(session, db_connection, cursor)  # Pass the session to the task function
        else:
            logging.error("Failed to establish database connection.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        if session:
            session.close()  # Ensure session is closed only after all task functions are done
        if db_connection and cursor:
            close_database_resources(db_connection, cursor)
        
def main():
    """
    The main entry point of the program.
    This function sets up the email callback and either launches the interactive window (in test mode) or sets up scheduled tasks (in normal mode).
    It controls the overall flow of the program based on the TEST_MODE flag.
    """
    # Set up the email callback
    setup_email_callback()

    if TEST_MODE:
        setup_interactive_window()
    else:
        # Schedule tasks to run periodically outside of TEST_MODE
        schedule.every(10).minutes.do(initialize_and_execute, process_unread_emails)
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Scheduler stopped manually.")

if __name__ == "__main__":
    main()
```

# login.py

```py
## login.py ##

from curl_cffi import requests
from selectolax.lexbor import LexborHTMLParser
from requests_toolbelt import MultipartEncoder
import os
import logging
import ctypes
from variables import *

def login_to_corrlinks():
    """
    Logs into the Corrlinks website and returns a session object.
    Returns:
    - requests.Session or None: A session object if login is successful, None otherwise

    This function sets up a requests session, configures it with necessary headers
    and proxy settings, and attempts to log in to the Corrlinks website. It handles
    retries for failed requests and verifies IP masking. The function returns the
    session object for use in subsequent requests.
    """
    try:
        path = os.path.abspath(os.path.dirname(__file__))
        ctypes.cdll.LoadLibrary(f'{path}\\{FINGERPRINT_DLL}')
        
        req = requests.Session()  # Initialize session here
        req.headers.update({
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        })

        if USE_PROXY and PROXY_URL:
            req.proxies = {'http': PROXY_URL, 'https': PROXY_URL}

        req.impersonate = 'chrome'
        req.base_url = BASE_URL
    
        # Verify IP masking by checking the external IP
        http_ip_response = req.get(HTTPBIN_IP_URL_HTTP)
        print('http', http_ip_response.json()['origin'])
        https_ip_response = req.get(HTTPBIN_IP_URL_HTTPS)
        print('https', https_ip_response.json()['origin'])

        # Attempt to log in
        while True:
            r = req.get(LOGIN_PAGE)
            if r.status_code == 200:
                print("Login page fetched successfully:", r.status_code)
                break
            print('retrying failed request...')
            req.headers.clear()
            req.cookies.clear()
    
        # Parse hidden fields and update data
        soup = LexborHTMLParser(r.content)
        data = {
            'ctl00$mainContentPlaceHolder$loginUserNameTextBox': USERNAME,
            'ctl00$mainContentPlaceHolder$loginPasswordTextBox': PASSWORD,
            'ctl00$mainContentPlaceHolder$loginButton': LOGIN_BUTTON_TEXT
        }
        data.update({x.attrs['name']: x.attrs['value'] for x in soup.css('input[type="hidden"]')})
        form = MultipartEncoder(fields=data)
        req.headers.update({'Content-Type': form.content_type})
        r = req.post(LOGIN_PAGE, data=form.to_string())
        print("Login attempt response:", r.status_code)

        # if r.status_code == 200:
        #     r = req.get(INBOX_PAGE)
        #     print("Accessed Inbox Page:", r.status_code)
        #     with open('r.html', 'w', encoding='utf-8') as f:
        #         f.write(r.text)
        #     print("Saved inbox content to r.html")

        return req  # Return the session object for further use
    except Exception as e:
        logging.error(f"An error occurred during login: {e}")
        return None  # It might be safer to return None or handle this more gracefully

if __name__ == "__main__":
    session = login_to_corrlinks()
    if session:
        print("Session initialized successfully.")
    else:
        print("Failed to initialize session.")

```

# accept_invite.py

```py
## accept_invite.py ##

import logging
import imaplib
import email
import time
import json
import os
from bs4 import BeautifulSoup
from requests import Session
from email.header import decode_header
from datetime import datetime, timedelta
from variables import *
from main import *
from db_ops import *
from login import *

# Set up logging
logging.basicConfig(filename='corrlinks_interaction.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def log_request_info(url, method, headers, data=None, params=None, cookies=None):
    """
    Logs detailed information about an HTTP request.
    Parameters:
    - url (str): The URL of the request
    - method (str): The HTTP method used (e.g., GET, POST)
    - headers (dict): The headers of the request
    - data (dict, optional): The form data of the request
    - params (dict, optional): The URL parameters of the request
    - cookies (dict, optional): The cookies sent with the request

    This function logs various components of an HTTP request for debugging purposes.
    It formats the information and writes it to the log file.
    """    
    logging.info(f"=== REQUEST INFO ({method}) ===")
    logging.info(f"URL: {url}")
    logging.info("Headers:")
    logging.info(json.dumps(dict(headers), indent=2))
    if data:
        logging.info("Form Data:")
        logging.info(json.dumps(data, indent=2))
    if params:
        logging.info("URL Parameters:")
        logging.info(json.dumps(params, indent=2))
    if cookies:
        logging.info("Cookies:")
        logging.info(json.dumps(dict(cookies), indent=2))
    logging.info("====================")

def log_response_info(response):
    """
    Logs detailed information about an HTTP response.
    Parameters:
    - response (requests.Response): The response object to log

    This function logs the status code, headers, cookies, and body of an HTTP response.
    It also attempts to extract and log any error messages from the response body.
    """
    logging.info("=== RESPONSE INFO ===")
    logging.info(f"Status Code: {response.status_code}")
    logging.info("Headers:")
    logging.info(json.dumps(dict(response.headers), indent=2))
    logging.info("Cookies:")
    logging.info(json.dumps(dict(response.cookies), indent=2))
    logging.info("Response Body:")
    logging.info(response.text[:2000])  # Log first 2000 characters of response
    
    # Try to extract more detailed error information
    if response.status_code != 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        error_msg = soup.find('div', class_='errortext')
        if error_msg:
            logging.error(f"Detailed error message: {error_msg.text}")
    
    logging.info("=====================")

def fetch_invite_code_and_name():
    """
    Retrieves an invite code and associated name from emails.
    Returns:
    - tuple: (invite_code, email_id, full_name) if found, (None, None, None) otherwise

    This function connects to an email server, searches for emails with specific subjects,
    and extracts invite codes and user names from these emails. It handles email parsing,
    decoding, and error logging.
    """
    logging.info("Starting to fetch invite code and name")
    try:
        mail = imaplib.IMAP4_SSL(EMAILURL0)
        logging.info(f"Connected to: {EMAILURL0}")
        
        mail.login(EMAIL0_USERNAME, EMAIL0_PASSWORD)
        logging.info(f"Logged in with username: {EMAIL0_USERNAME}")
        
        mail.select("inbox")
        logging.info("Selected inbox")
        
        # First, let's get all emails from the last 7 days
        date_since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{date_since}")')
        email_ids = messages[0].split()
        logging.info(f"Total emails in the last 30 days: {len(email_ids)}")
        
        # Search for emails with the subject "Person in Custody:"
        status, messages = mail.search(None, f'(SUBJECT "Person in Custody:" SINCE "{date_since}")')
        invite_email_ids = messages[0].split()
        logging.info(f"Search status: {status}, Number of invite messages found: {len(invite_email_ids)}")
        
        if not invite_email_ids:
            logging.info("No emails found with exact subject. Trying a broader search.")
            status, messages = mail.search(None, f'(SUBJECT "Custody" SINCE "{date_since}")')
            invite_email_ids = messages[0].split()
            logging.info(f"Broader search status: {status}, Number of potential invite messages found: {len(invite_email_ids)}")
        
        # Sort emails by date, newest first
        invite_email_ids.sort(key=lambda x: int(x), reverse=True)
        
        for email_id in invite_email_ids:
            logging.info(f"Processing invite email ID: {email_id}")
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            logging.info(f"Fetch status: {status}")
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_header(msg['Subject'])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    date = email.utils.parsedate_to_datetime(msg['Date'])
                    logging.info(f"Email subject: {subject}, Date: {date}")
                    
                    if "Person in Custody:" in subject:
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                        else:
                            body = msg.get_payload(decode=True).decode()
                        
                        # Extract invite code
                        invite_code_line = [line for line in body.split('\n') if "Identification Code:" in line]
                        if invite_code_line:
                            invite_code = invite_code_line[0].split(":")[1].strip()
                            logging.info(f"Found invite code: {invite_code}")
                            
                            # Extract full name from subject
                            name_part = subject.split(":")[1].strip()
                            last_name, first_name = name_part.split(", ")
                            full_name = f"{first_name} {last_name}"
                            logging.info(f"Extracted full name: {full_name}")
                            
                            return invite_code, email_id, full_name
                    else:
                        logging.info(f"Email subject does not match exactly: {subject}")
        
        logging.info("No invite found in any emails")
        return None, None, None
    except Exception as e:
        logging.error(f"An error occurred while fetching invite: {str(e)}")
        return None, None, None
    finally:
        try:
            mail.logout()
            logging.info("Logged out from mail server")
        except:
            pass

def extract_form_data(html):
    """
    Extracts form data from an HTML page.
    Parameters:
    - html (str): The HTML content to parse

    Returns:
    - dict: A dictionary of form field names and their values

    This function uses BeautifulSoup to parse the HTML and extract all input fields
    from a form with the id 'aspnetForm'. It's used to prepare data for form submissions.
    """
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find('form', id='aspnetForm')
    if not form:
        logging.warning("Form not found in HTML")
        return {}
    
    form_data = {}
    for input_tag in form.find_all('input'):
        name = input_tag.get('name')
        value = input_tag.get('value', '')
        if name:
            form_data[name] = value
    
    logging.info("Extracted Form Data:")
    logging.info(json.dumps(form_data, indent=2))
    return form_data
        
def navigate_to_pending_contact(session):
    """
    Navigates to the Pending Contact page on the Corrlinks website.
    Parameters:
    - session (requests.Session): The session object for making requests

    Returns:
    - tuple: (response, form_data) if successful, (None, None) if session expired

    This function sends a GET request to the Pending Contact page, checks if the session is still valid,
    and extracts the form data from the response. It logs detailed request and response information.
    """
    logging.info("Navigating to Pending Contact page")
    logging.info(f"Session cookies before navigation: {dict(session.cookies)}")
    response = session.get(CONTACT_URL)
    logging.info(f"Session cookies after navigation: {dict(session.cookies)}")
    
    # Check if we're still logged in
    if "Login" in response.text:
        logging.error("Session appears to have expired. Need to re-login.")
        return None, None
    
    log_request_info(CONTACT_URL, "GET", dict(response.request.headers), 
                     cookies=session.cookies)
    log_response_info(response)
    
    form_data = extract_form_data(response.text)
    
    return response, form_data

def enter_invite_code(session, form_data, invite_code):
    """
    Enters an invite code on the Pending Contact page.
    Parameters:
    - session (requests.Session): The session object for making requests
    - form_data (dict): The form data extracted from the page
    - invite_code (str): The invite code to enter

    Returns:
    - tuple: (response, bool) where bool indicates if the invite code was successfully entered

    This function submits the invite code to the website, handles the response,
    and checks if the inmate details are present in the response. It includes retry logic
    for handling intermittent failures.
    """
    logging.info(f"Entering invite code: {invite_code}")
    logging.info(f"Session cookies before entering invite code: {dict(session.cookies)}")

    data = form_data.copy()
    data.update({
        'ctl00$topScriptManager': 'ctl00$topUpdatePanel|ctl00$mainContentPlaceHolder$PendingContactUC1$SearchButton',
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        'DES_Group': 'ADDINMATECONTROLGROUP',
        'ctl00$mainContentPlaceHolder$PendingContactUC1$InmateNumberTextBox': invite_code,
        '__ASYNCPOST': 'true',
        'ctl00$mainContentPlaceHolder$PendingContactUC1$SearchButton': 'Go'
    })

    headers = session.headers.copy()
    headers.update({
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-MicrosoftAjax': 'Delta=true',
        'X-Requested-With': 'XMLHttpRequest'
    })

    log_request_info(CONTACT_URL, "POST", headers, data=data)
    response = session.post(CONTACT_URL, data=data, headers=headers)
    logging.info(f"Session cookies after entering invite code: {dict(session.cookies)}")
    log_response_info(response)

    # Save the HTML response to a file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"invite_code_response_{timestamp}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(response.text)
    logging.info(f"Saved HTML response to {filename}")

    # More detailed response parsing
    soup = BeautifulSoup(response.text, 'html.parser')
    main_content = soup.find('div', {'id': 'ctl00_mainContentPlaceHolder_mainPanel'})
    if main_content:
        logging.debug(f"Main content area: {main_content.text[:500]}")
    else:
        logging.warning("Main content area not found in response")

    # Check for specific error messages
    error_msg = soup.find('span', {'id': 'ctl00_mainContentPlaceHolder_PendingContactUC1_errorLabel'})
    if error_msg and error_msg.text.strip():
        logging.error(f"Error message found: {error_msg.text.strip()}")
        return response, False

    # Check for inmate details
    inmate_name = soup.find('span', {'id': 'ctl00_mainContentPlaceHolder_PendingContactUC1_inmateNameDataLabel'})
    inmate_number = soup.find('span', {'id': 'ctl00_mainContentPlaceHolder_PendingContactUC1_inmateNumberDataLabel'})

    if inmate_name and inmate_number:
        logging.info(f"Inmate details found: Name - {inmate_name.text.strip()}, Number - {inmate_number.text.strip()}")
        return response, True
    else:
        logging.error("Inmate details not found in the response")
        # Log a portion of the response for debugging
        logging.debug(f"Response content: {response.text[:1000]}")

        # Retry logic for intermittent failures
        max_retries = 3
        for attempt in range(max_retries):
            logging.warning(f"Retrying invite code entry. Attempt {attempt + 1} of {max_retries}")
            response = session.post(CONTACT_URL, data=data, headers=headers)
            log_response_info(response)

            # Check for inmate details again
            soup = BeautifulSoup(response.text, 'html.parser')
            inmate_name = soup.find('span', {'id': 'ctl00_mainContentPlaceHolder_PendingContactUC1_inmateNameDataLabel'})
            inmate_number = soup.find('span', {'id': 'ctl00_mainContentPlaceHolder_PendingContactUC1_inmateNumberDataLabel'})

            if inmate_name and inmate_number:
                logging.info(f"Inmate details found on retry: Name - {inmate_name.text.strip()}, Number - {inmate_number.text.strip()}")
                return response, True
            time.sleep(2)  # Delay before next retry

        return response, False

def accept_invitation(session, form_data, invite_code):
    """
    Accepts an invitation on the Corrlinks website.
    Parameters:
    - session (requests.Session): The session object for making requests
    - form_data (dict): The form data extracted from the page
    - invite_code (str): The invite code of the invitation to accept

    Returns:
    - bool: True if the invitation was successfully accepted, False otherwise

    This function submits the request to accept an invitation, handles the response,
    and checks for confirmation of successful acceptance. It logs detailed information
    about the request and response for debugging purposes.
    """
    logging.info("Accepting invitation")
    
    # Re-fetch the page to get the most up-to-date form data
    response, updated_form_data = navigate_to_pending_contact(session)

    # Extract necessary data from the updated form
    viewstate = updated_form_data.get('__VIEWSTATE', '')
    compressedviewstate = updated_form_data.get('__COMPRESSEDVIEWSTATE', '')
    
    # Prepare the data for the accept request
    accept_data = {
        '__EVENTTARGET': 'ctl00$mainContentPlaceHolder$PendingContactUC1$addInmateButton',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': viewstate,
        '__COMPRESSEDVIEWSTATE': compressedviewstate,
        'DES_Group': 'SEARCHRESULTGROUP',
        'ctl00$mainContentPlaceHolder$PendingContactUC1$InmateNumberTextBox': invite_code,
    }
    
    # Add any other necessary form fields from updated_form_data
    for key, value in updated_form_data.items():
        if key not in accept_data:
            accept_data[key] = value

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.corrlinks.com/PendingContact.aspx',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
        'X-MicrosoftAjax': 'Delta=true'
    }
    
    # Ensure all necessary cookies are included
    for cookie in session.cookies:
        logging.info(f"Cookie being sent: {cookie.name}={cookie.value}")

    logging.info("Sending accept request")
    log_request_info(CONTACT_URL, "POST", headers, data=accept_data)
    response = session.post(CONTACT_URL, data=accept_data, headers=headers)
    log_response_info(response)
    
    if response.status_code == 200:
        if "Contact request accepted" in response.text:
            logging.info("Invitation accepted successfully")
            return True
        else:
            logging.warning("Unexpected response content. Manual verification needed.")
            # Save the response content for debugging
            with open('accept_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logging.info("Response content saved to accept_response.html")
            return False
    else:
        logging.error(f"Error accepting invitation: Status {response.status_code}")
        return False

def process_invitation():
    """
    Processes an invitation from start to finish.
    Returns:
    - bool: True if the invitation was successfully processed, False otherwise

    This function orchestrates the entire invitation process. It fetches the invite code and name,
    logs into Corrlinks, navigates to the pending contact page, enters the invite code,
    and accepts the invitation. It handles session management and error logging throughout the process.
    """
    invite_code, email_id, full_name = fetch_invite_code_and_name()
    if not invite_code:
        logging.error("Failed to fetch invite code")
        return False

    session = login_to_corrlinks()
    if not session:
        logging.error("Failed to login to Corrlinks")
        return False

    logging.info(f"Session cookies after login: {dict(session.cookies)}")

    response, form_data = navigate_to_pending_contact(session)
    if response is None or form_data is None:
        logging.error("Failed to navigate to Pending Contact page or session expired")
        return False

    time.sleep(2)

    response, invite_code_entered = enter_invite_code(session, form_data, invite_code)
    if not invite_code_entered:
        logging.error("Failed to enter invite code or invite code not recognized")
        return False

    logging.info(f"Session cookies after entering invite code: {dict(session.cookies)}")

    time.sleep(2)
    
    max_retries = 3
    for attempt in range(max_retries):
        response, invite_code_entered = enter_invite_code(session, form_data, invite_code)
        if invite_code_entered:
            break
        logging.warning(f"Attempt {attempt + 1} failed. Retrying...")
        time.sleep(2)  # Wait before retrying

    if not invite_code_entered:
        logging.error("Failed to enter invite code after multiple attempts")
        return False

    success = accept_invitation(session, form_data, invite_code)
    if success:
        delete_invite_email(email_id)
        logging.info(f"Successfully processed invitation for {full_name}")
        return True
    else:
        logging.error(f"Failed to accept invitation for {full_name}")
        return False
    
def delete_invite_email(email_id):
    """
    Deletes the invite email after successful processing.
    Parameters:
    - email_id (str): The ID of the email to delete

    This function connects to the email server, marks the specified email for deletion,
    and permanently removes it. It's called after an invitation has been successfully processed
    to clean up the inbox.
    """
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(EMAILURL0)
        # Login to your account
        mail.login(EMAIL0_USERNAME, EMAIL0_PASSWORD)
        # Select the mailbox you want to use
        mail.select("inbox")
        # Mark the specific email for deletion
        mail.store(email_id, '+FLAGS', '\\Deleted')
        # Permanently remove emails marked for deletion
        mail.expunge()
        logging.info(f"Successfully deleted invite email with ID: {email_id}")
    except Exception as e:
        logging.error(f"Failed to delete invite email: {str(e)}")
    finally:
        mail.logout()
        
if __name__ == "__main__":
    result = process_invitation()
    print("Invitation processing result:", result)
```

# pull_email.py

```py
## pull_email.py ##

import re
import logging
from selectolax.lexbor import LexborHTMLParser
from requests_toolbelt import MultipartEncoder
from variables import *
from db_ops import *
from send_sms import *
from accept_invite import *

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.5',
    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    'X-MicrosoftAjax': 'Delta=true',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Referer': 'INBOX_URL'
}

def process_unread_emails(session, db_connection, cursor):
    """
    Processes unread emails from the Corrlinks inbox.
    Parameters:
    - session (requests.Session): The session object for making requests
    - db_connection: The database connection object
    - cursor: The database cursor object

    This function fetches the inbox page, extracts email data, and processes each unread email.
    It handles parsing of AJAX responses, extracting email content, and saving processed emails to the database.
    The function also respects the TEST_MODE setting for limiting the number of emails processed.
    """
    try:
        logging.info(f"Attempting to fetch inbox page: {INBOX_URL}")
        response = session.get(INBOX_URL)
        logging.info(f"Inbox page response status code: {response.status_code}")
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch the inbox page, status code: {response.status_code}")
            raise Exception(f"Failed to fetch the inbox page, status code: {response.status_code}")
        
        # Prints the HTML content of the inbox page
        # with open('inbox.html', 'w', encoding='utf-8') as f:
        #     f.write(response.text)
        # logging.info("Saved inbox content to inbox.html")
        
        parser = LexborHTMLParser(response.text)
        
        # Extract COMPRESSEDVIEWSTATE
        compressed_viewstate = parser.css_first('input[name="__COMPRESSEDVIEWSTATE"]')
        
        if compressed_viewstate:
            compressed_viewstate_value = compressed_viewstate.attributes.get('value', '')
            logging.debug(f"COMPRESSEDVIEWSTATE found, length: {len(compressed_viewstate_value)}")
        else:
            logging.error("COMPRESSEDVIEWSTATE not found in the HTML.")
            raise Exception("COMPRESSEDVIEWSTATE not found in the HTML")
        
        # Find all email rows
        email_rows = parser.css('tr[onmouseover^="this.className=\'MessageDataGrid ItemHighlighted\'"]')
        logging.info(f"Found {len(email_rows)} email rows")
        
        if not email_rows:
            logging.error("No email rows found.")
            raise Exception("No email rows found in the HTML")
        
        emails_to_save = []  # Initialize the list to store emails for saving
        
        for i, row in enumerate(email_rows):
            logging.debug(f"Processing email row {i+1}")
            if TEST_MODE and i >= 3:
                logging.info("Test mode: stopping after 3 emails")
                break
            
            # Extract message ID from the tr element
            row_html = row.html
            message_id_match = re.search(r'(Command="REPLY"\s+MessageId="(\d+)"|messageid="(\d+)")', row_html, re.IGNORECASE)
            
            if message_id_match:
                message_id = message_id_match.group(2) or message_id_match.group(3)
                logging.debug(f"Found MessageId: {message_id}")
            else:
                message_id = None
                logging.error(f"MessageId not found in row {i+1}.")

            # Extract other details
            from_elem = row.css_first('th.MessageDataGrid.Item a.tooltip span')
            subject_elem = row.css_first('td.MessageDataGrid.Item a.tooltip span')
            date_elem = row.css_first('td.MessageDataGrid.Item:nth-child(4)')
            
            from_text = from_elem.text() if from_elem else 'Not found'
            subject_text = subject_elem.text() if subject_elem else 'Not found'
            date_text = date_elem.text() if date_elem else 'Not found'
            
            logging.info(f"Extracted email data: MessageId={message_id}, From={from_text}, Subject={subject_text}, Date={date_text}")
            
            if message_id:
                # Construct POST data
                post_data = {
                    '__EVENTTARGET': 'ctl00$mainContentPlaceHolder$inboxGridView',
                    '__EVENTARGUMENT': f'rc{i}',
                    '__COMPRESSEDVIEWSTATE': compressed_viewstate_value,
                    '__ASYNCPOST': 'true',
                    'ctl00$topScriptManager': 'ctl00$mainContentPlaceHolder$inboxGridView'
                }
                
                form = MultipartEncoder(fields=post_data)
                headers = HEADERS.copy()
                headers['Content-Type'] = form.content_type
                
                logging.info(f"Sending POST request for email {message_id}")
                email_response = session.post(INBOX_URL, data=form.to_string(), headers=headers)
                logging.info(f"Email response status code: {email_response.status_code}")
                
                if email_response.status_code == 200:
                    # Save email content to file
                    # with open(f'email_{message_id}.html', 'w', encoding='utf-8') as f:
                    #     f.write(email_response.text)
                    # logging.info(f"Saved email content to email_{message_id}.html")
                    
                    # Parse the AJAX response
                    email_content = parse_ajax_response(email_response.text)
                    if email_content:
                        email_data = process_email_content(email_content, message_id)
                        if email_data:
                            # Ensure user exists in the database
                            user_id = ensure_user_exists(db_connection, cursor, email_data['from'])
                            if user_id:
                                # Prepare email data for saving
                                email_to_save = {
                                    'user_id': user_id,
                                    'sent_datetime': email_data['date'],
                                    'subject': email_data['subject'],
                                    'body': email_data['message'],
                                    'message_id': email_data['message_id']
                                }
                                emails_to_save.append(email_to_save)
                                logging.info(f"Processed email: {email_to_save}")
                            else:
                                logging.warning(f"Failed to ensure user exists for email: {email_data['message_id']}")
                        else:
                            logging.warning(f"Failed to process email content for message ID {message_id}")
                    else:
                        logging.error(f"Failed to parse AJAX response for message ID {message_id}")
                else:
                    logging.error(f"Failed to fetch email content, status code: {email_response.status_code}")
            
            else:
                logging.warning(f"Failed to extract message ID for email {i+1}")

            if TEST_MODE and i >= 2:
                logging.info("Test mode: stopping after 3 emails")
                break

        # Save all processed emails to the database
        if emails_to_save:
            save_emails(emails_to_save, db_connection, cursor)
        
    except Exception as e:
        logging.error(f"An error occurred while processing emails: {str(e)}", exc_info=True)

def parse_ajax_response(response_text):
    """
    Parses the AJAX response to extract the relevant HTML content.
    Parameters:
    - response_text (str): The full text of the AJAX response

    Returns:
    - str: The extracted HTML content, or None if not found

    This function uses a regular expression to extract the HTML content from the AJAX response.
    It's used to isolate the email content from the full page update returned by the server.
    """
    match = re.search(r'\|updatePanel\|ctl00_topUpdatePanel\|(.*?)\|', response_text, re.DOTALL)
    if match:
        return match.group(1)
    return None

def process_email_content(content, message_id):
    """
    Processes the content of a single email.
    Parameters:
    - content (str): The HTML content of the email
    - message_id (str): The unique identifier of the email

    Returns:
    - dict: A dictionary containing the parsed email data

    This function extracts various components of an email (from, date, subject, message)
    from the HTML content. It also calls extract_most_recent_message to isolate the latest
    part of threaded conversations.
    """
    parser = LexborHTMLParser(content)
    
    from_text = parser.css_first('#ctl00_mainContentPlaceHolder_fromTextBox')
    date_text = parser.css_first('#ctl00_mainContentPlaceHolder_dateTextBox')
    subject_text = parser.css_first('#ctl00_mainContentPlaceHolder_subjectTextBox')
    message_text = parser.css_first('#ctl00_mainContentPlaceHolder_messageTextBox')
    
    full_message = message_text.text() if message_text else 'Not found'
    
    # Extract only the most recent message
    most_recent_message = extract_most_recent_message(full_message)
    
    result = {
        'message_id': message_id,
        'from': from_text.attributes.get('value') if from_text else 'Not found',
        'date': date_text.attributes.get('value') if date_text else 'Not found',
        'subject': subject_text.attributes.get('value') if subject_text else 'Not found',
        'message': most_recent_message
    }
    
    logging.debug(f"Processed email content: {result}")
    return result

def extract_most_recent_message(full_message):
    """
    Extracts the most recent message from a potentially threaded email conversation.
    Parameters:
    - full_message (str): The full text of the email message

    Returns:
    - str: The extracted most recent message

    This function uses regular expressions to identify common reply indicators and
    splits the message to isolate the most recent part. It's useful for handling
    threaded email conversations.
    """
    # Split the message by common reply indicators
    patterns = [
        r'-----.*?on \d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2} (AM|PM) wrote:',
        r'.*? on \d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2} (AM|PM) wrote',
        r'>',  # This catches the '>' character often used in replies
    ]
    
    for pattern in patterns:
        parts = re.split(pattern, full_message, maxsplit=1, flags=re.IGNORECASE | re.DOTALL)
        if len(parts) > 1:
            return parts[0].strip()
    
    # If no split occurred, return the entire message
    return full_message.strip()

if __name__ == "__main__":
    invite_code, email_id, full_name = fetch_invite_code_and_name()
    if invite_code and full_name:
        print(f"Invite Code: {invite_code}")
        print(f"User Name: {full_name}")
        accept_invitation(invite_code, email_id, full_name)
```

# fingerprint.dll

This is a binary file of the type: Dynamic-link Library

# send_sms.py

```py
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
```

# variables.py

```py
## variables.py ##

import os
from twilio.rest import Client

# URL settings
LOGIN_URL = "https://www.corrlinks.com/Login.aspx"
INBOX_URL = "https://www.corrlinks.com/Inbox.aspx"
DEFAULT_URL = "https://www.corrlinks.com/Default.aspx"
UNREAD_MESSAGES_URL = "https://www.corrlinks.com/Inbox.aspx?UnreadMessages"
REPLY_URL_BASE = "https://www.corrlinks.com/NewMessage.aspx?messageId={message_id}&type=reply"
MESSAGE_PROCESSED = "https://www.corrlinks.com/MessageProcessed.aspx?type=send"
CONTACT_URL = "https://www.corrlinks.com/PendingContact.aspx"
TEST_REPLY_WEBHOOK_URL = "https://webhook.site/5eb549e9-09aa-4fe1-9bec-bcb5981d252a"
REPLY_WEBHOOK_URL = "https://smsreceiverapi.contxts.net/api/sms"
SMS_SEND_URL = 'https://textbelt.com/text'
SMS_STATUS_URL = 'https://textbelt.com/status/{}'
SMS_QUOTA_URL = 'https://textbelt.com/quota/{}'
SMS_RETRY_DELAY = 120  # seconds
MAX_SMS_RETRIES = 3

# Credentials for login
USERNAME = "bradleyaroth@gmail.com"
PASSWORD = "Thought20"
# USERNAME = "info@contxts.net"
# PASSWORD = "ConTXTsR0ck$"
LOGIN_BUTTON_TEXT = 'Login >>'

# Proxy settings
PROXY_URL = 'http://Glenna:r3orm8Ot2j=WmgJcO5@us.smartproxy.com:10000'

# URLs
BASE_URL = 'https://www.corrlinks.com/'
LOGIN_PAGE = 'Login.aspx'
INBOX_PAGE = 'Inbox.aspx'
HTTPBIN_IP_URL_HTTP = 'http://httpbin.org/ip'
HTTPBIN_IP_URL_HTTPS = 'https://httpbin.org/ip'

# Path to the DLL
FINGERPRINT_DLL = 'fingerprint.dll'

# Application behavior flags
CHECK_UNREAD_FLAG = True  # Flag to determine if unread messages should be checked
TEST_MODE = True  # Flag to enable test mode, which affects how emails are processed
USE_PROXY = False  # Flag to enable or disable proxy use during the login process

# Static MessageID for testing
STATIC_MESSAGE_ID = "3706018280"

# Database Connection Variables
DB_IP = "SQL1.reliantrack.local"
DB_USERNAME = "sa"
DB_PASSWORD = "Gr3@tSc0tch"
DB_NAME = "ConTXT"


# Consolidated Database Settings for import
DB_SETTINGS = {
    "DB_IP": DB_IP,
    "DB_USERNAME": DB_USERNAME,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_NAME": DB_NAME,
    "CONN_STR": f"DRIVER={{SQL Server}};SERVER={DB_IP};DATABASE={DB_NAME};UID={DB_USERNAME};PWD={DB_PASSWORD}"
}

# SMS Auth
API_KEY = '3383a22f7ee0a5da47b11a90ce451b62df3cf185XVOK7QpjQSjJ2eNkHPSaQ9Jur'
TEST_TO_NUMBER = '4024312303'
TEST_KEY = '3383a22f7ee0a5da47b11a90ce451b62df3cf185XVOK7QpjQSjJ2eNkHPSaQ9Jur_test'
TEST_MESSAGE_BODY = 'Sending Test Message From ConTXT'
TEST_USER_ID = '15372010'

# BOT Email Account Credentials
EMAILURL0 = "mail.contxts.net"
EMIALURL1 = "smtp.gmail.com"
EMAIL0_USERNAME = "bradley@contxts.net"
EMAIL0_PASSWORD = "Gr3@tSc0tch"
EMAIL1_USERNAME = "bradleyaroth@gmail.com"
EMAIL1_PASSWORD = "knxq vmyu eigo tawz"
EMAIL2_USERNAME = "XYZCorrlink@gmail.com"
EMAIL2_PASSWORD = "123456PasswordPleaseChangeThis"
EMAIL3_USERNAME = "XYZCorrlink@gmail.com"
EMAIL3_PASSWORD = "123456PasswordPleaseChangeThis"
EMAIL4_USERNAME = "XYZCorrlink@gmail.com"
EMAIL4_PASSWORD = "123456PasswordPleaseChangeThis"
EMAIL5_USERNAME = "XYZCorrlink@gmail.com"
EMAIL5_PASSWORD = "123456PasswordPleaseChangeThis"
```

