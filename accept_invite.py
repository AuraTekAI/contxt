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