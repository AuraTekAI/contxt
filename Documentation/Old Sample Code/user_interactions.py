import pyodbc
import logging
import re
from typing import List, Dict
from datetime import datetime, timedelta
from variables import *
from db_ops import *
from sending_email import send_email_responses

# Setting up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_contact_emails(driver, db_connection, cursor):
    """
    Fetches and parses contact emails to extract contact information.
    Ensures all emails are processed before closing the connection.
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

def insert_contacts_to_db(contacts: List[Dict], db_connection, user_id: int):
    """
    Inserts the contact information into the database after checking for duplicates.
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
        send_email_responses(driver, db_connection, cursor, user_id, message_content)

def send_contact_list_email(user_id, db_connection, driver, cursor):
    """
    Sends an email containing the user's current contact list.
    """
    cursor.execute("SELECT ContactName, PhoneNumber, EmailAddress FROM Contacts WHERE UserID = ?", (user_id,))
    contacts = cursor.fetchall()
    contact_list = "\n".join([f"{name} - {phone} - {email}" for name, phone, email in contacts])
    message_content = f"Your current contact list:\n{contact_list}"
    logging.info(f"Drafting contact list email for user {user_id}: {message_content}")
    send_email_responses(driver, db_connection, cursor, user_id, message_content)

def remove_contact_from_db(contact_name, db_connection, user_id, driver, cursor):
    """
    Removes a contact from the database.
    """
    cursor.execute("DELETE FROM Contacts WHERE UserID = ? AND ContactName = ?", (user_id, contact_name))
    db_connection.commit()
    logging.info(f"Removed contact {contact_name} for user ID {user_id}.")
    message_content = f"The contact '{contact_name}' has been removed from your contact list."
    send_email_responses(driver, db_connection, cursor, user_id, message_content)

def add_contact_email(email_body, db_connection, user_id, driver, cursor):
    """
    Adds a contact email to the database.
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
    """
    lines = email_body.splitlines()
    if len(lines) >= 2:
        contact_name = lines[0].strip()
        phone = lines[1].strip()
        contact = {'ContactName': contact_name, 'PhoneNumber': phone}
        insert_contacts_to_db([contact], db_connection, user_id)
        send_contact_list_email(user_id, db_connection, driver, cursor)

def set_screen_name(body, db_connection, user_id, driver, cursor):
    """
    Sets the screen name for the user.
    """
    cursor.execute("UPDATE Users SET ScreenName = ? WHERE UserID = ?", (body.strip(), user_id))
    db_connection.commit()
    logging.info(f"Screen name set to {body.strip()} for user ID {user_id}.")
    message_content = f"Your screen name has been set to {body.strip()}."
    send_email_responses(driver, db_connection, cursor, user_id, message_content)

def set_private_mode(user_id, db_connection, driver, cursor):
    """
    Sets the user to private mode.
    """
    cursor.execute("UPDATE Users SET PrivateMode = 'Y' WHERE UserID = ?", (user_id,))
    db_connection.commit()
    logging.info(f"User ID {user_id} set to private mode.")
    message_content = "Your account has been set to private mode."
    send_email_responses(driver, db_connection, cursor, user_id, message_content)
