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
