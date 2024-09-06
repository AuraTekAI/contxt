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