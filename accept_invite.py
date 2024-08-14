## accept_invite.py ##

from utils.helper_functions import convert_cookies_to_splash_format

import logging
import imaplib
import email
import json
from selectolax.lexbor import LexborHTMLParser
from email.header import decode_header
from datetime import datetime, timedelta
from variables import *
from login import *

# Set up logging
logging.basicConfig(filename='corrlinks_interaction.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class MailBox:
    """
    A class to interact with an email inbox using the IMAP protocol.
    
    This class provides functionalities to connect to an email server, log in, 
    retrieve, process, and delete emails. It is designed to handle emails containing
    invitation codes and extract relevant details such as the invite code and full name.
    
    Parameters:
    - user_name (str): The username/email address for the mailbox.
    - password (str): The password for the mailbox.
    - email_url (str): The IMAP URL of the email service provider.
    """
    def __init__(self, user_name, password, email_url):
        """
        Initializes the MailBox class with user credentials and server URL.
        
        Parameters:
        - user_name (str): The username/email address for the mailbox.
        - password (str): The password for the mailbox.
        - email_url (str): The IMAP URL of the email service provider.
        
        Initializes instance variables to store user credentials, email server URL,
        and a placeholder for the mailbox connection.
        """
        self.user_name = user_name
        self.password = password
        self.email_url = email_url
        self.mail = None

    def __enter__(self):
        """
        Establishes a connection to the mailbox and logs in.
        
        Returns:
        - MailBox: The instance of the MailBox class with an active connection.
        
        This method is called when entering the context of a 'with' statement.
        It connects to the mailbox and logs in using the provided credentials.
        """
        self.mail = self.get_mailbox_with_url()
        self.login_mailbox()
        logging.info("Logged in mailbox")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Logs out from the mailbox and closes the connection.
        
        This method is called when exiting the context of a 'with' statement.
        It ensures that the mailbox connection is properly closed.
        """
        self.mail.logout()
        logging.info("Logged out from mailbox")

    def get_mailbox_with_url(self):
        """
        Connects to the mailbox using the specified email URL.
        
        Returns:
        - imaplib.IMAP4_SSL: An IMAP connection object.
        
        Raises:
        - Exception: If the connection to the email server fails.
        
        This method establishes a secure connection to the email server using IMAP4_SSL.
        """
        try:
            mail = imaplib.IMAP4_SSL(self.email_url)
            logging.info(f"Connected to: {self.email_url}")
            return mail
        except Exception as e:
            logging.error(f"Failed to connect to {self.email_url}: {e}")
            raise

    def login_mailbox(self):
        """
        Logs in to the mailbox using the provided username and password.
        
        Raises:
        - Exception: If the login process fails.
        
        This method logs in to the mailbox using the credentials provided during 
        the initialization of the class.
        """
        try:
            self.mail.login(self.user_name, self.password)
            logging.info(f"Logged in as {self.user_name}")
        except Exception as e:
            logging.error(f"Login failed for {self.user_name}: {e}")
            raise
    
    def get_inbox(self):
        """
        Selects the inbox folder within the mailbox.
        
        Raises:
        - Exception: If the inbox cannot be selected.
        
        This method selects the "inbox" folder in the mailbox, preparing it 
        for operations such as searching or fetching emails.
        """
        try:
            self.mail.select("inbox")
            logging.info("Selected inbox")
        except Exception as e:
            logging.error(f"Failed to select inbox: {e}")
            raise
    
    def days_filter_value(self, days):
        """
        Generates a date filter string for searching emails.
        
        Parameters:
        - days (int): The number of days to subtract from the current date.
        
        Returns:
        - str: A date string in the format 'DD-MMM-YYYY'.
        
        This method returns a date string used to filter emails based on their 
        age relative to the current date.
        """
        return (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")

    def search_mail_using_date_text_value(self, days, text_value):
        """
        Searches for emails in the inbox based on date and text criteria.
        
        Parameters:
        - days (int): The number of days to look back from today.
        - text_value (str): The text to search for within the emails.
        
        Returns:
        - list: A list of email IDs that match the search criteria.
        
        Raises:
        - Exception: If the search fails.
        
        This method searches the inbox for emails that match the specified 
        date and text criteria, returning a list of matching email IDs.
        """
        try:
            date = self.days_filter_value(days)
            status, messages = self.mail.search(None, f'{text_value} "{date}")')
            if status == "OK":
                logging.info(f"Found {len(messages[0].split())} messages matching criteria.")
                return messages[0].split()
            else:
                logging.warning("No messages found matching criteria.")
                return []
        except Exception as e:
            logging.error(f"Failed to search mail: {e}.")
            raise

    def sort_email_ids(self, email_ids):
        """
        Sorts a list of email IDs in descending order.
        
        Parameters:
        - email_ids (list): A list of email IDs (as strings) to be sorted.
        
        Returns:
        - list: The sorted list of email IDs in descending order.
        
        Raises:
        - ValueError: If the email IDs cannot be converted to integers.
        
        This method sorts the provided list of email IDs in descending order,
        which is used to process the most recent emails first.
        """
        try:
            sorted_ids = sorted(email_ids, key=lambda x: int(x), reverse=True)
            logging.info(f"Sorted email IDs: {sorted_ids}")
            return sorted_ids
        except ValueError as e:
            logging.error(f"Failed to sort email IDs: {e}")
            raise
    
    def fetch_email(self, email_id):
        """
        Fetches the full content of an email by its ID.
        
        Parameters:
        - email_id (str): The ID of the email to be fetched.
        
        Returns:
        - list: A list of tuples containing the raw email data.
        
        Raises:
        - Exception: If fetching the email fails.
        
        This method retrieves the complete email message, including headers and body,
        for the given email ID.
        """
        try:
            logging.info(f"Processing invite email ID: {email_id}")
            status, msg_data = self.mail.fetch(email_id, "(RFC822)")
            logging.info(f"Fetch status: {status}")
            if status == "OK":
                return msg_data
            else:
                logging.error(f"Failed to fetch email ID {email_id}: {status}")
                return None
        except Exception as e:
            logging.error(f"Error fetching email ID {email_id}: {e}")
            raise
    
    def process_email(self, msg_data):
        """
        Processes an email to extract the subject, date, and body content.
        
        Parameters:
        - msg_data (list): The raw email data fetched from the server.
        
        Returns:
        - tuple: A tuple containing the invite code and full name if found, otherwise None.
        
        Raises:
        - Exception: If processing the email fails.
        
        This method processes the fetched email data to extract the subject, date,
        and body. It checks for specific content related to invitations and extracts
        the invite code and the full name of the person.
        """
        try:
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, date = self.extract_subject_and_date(msg)
                    if "Person in Custody:" in subject:
                        body = self.get_email_body(msg)
                        invite_code, full_name = self.extract_invite_code_and_name(subject, body)
                        if invite_code and full_name:
                            return invite_code, full_name
        except Exception as e:
            logging.error(f"Error processing email: {e}")
            raise
    
    def extract_subject_and_date(self, msg):
        """
        Extracts and decodes the subject and date from an email.
        
        Parameters:
        - msg (email.message.EmailMessage): The email message object.
        
        Returns:
        - tuple: A tuple containing the decoded subject (str) and date (datetime).
        
        This method extracts and decodes the subject and date from the email's headers.
        """
        subject = decode_header(msg['Subject'])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()
        date = email.utils.parsedate_to_datetime(msg['Date'])
        logging.info(f"Email subject: {subject}, Date: {date}")
        return subject, date
    
    def get_email_body(self, msg):
        """
        Retrieves the email body, handling both plain text and multipart messages.
        
        Parameters:
        - msg (email.message.EmailMessage): The email message object.
        
        Returns:
        - str: The decoded email body content.
        
        Raises:
        - Exception: If the body cannot be retrieved or decoded.
        
        This method retrieves the body of the email, handling multipart messages to extract 
        the relevant text content.
        """
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        return part.get_payload(decode=True).decode()
            else:
                return msg.get_payload(decode=True).decode()
        except Exception as e:
            logging.error(f"Failed to get email body: {e}")
            raise
    
    def extract_invite_code_and_name(self, subject, body):
        """
        Extracts the invite code and full name from the email subject and body.
        
        Parameters:
        - subject (str): The decoded subject of the email.
        - body (str): The decoded body content of the email.
        
        Returns:
        - tuple: A tuple containing the invite code (str) and full name (str).
        
        Raises:
        - Exception: If the invite code or full name cannot be extracted.
        
        This method searches the email body for an invite code and extracts the full name 
        from the subject. It returns both values if found.
        """
        try:
            invite_code_line = [line for line in body.split('\n') if "Identification Code:" in line]
            if invite_code_line:
                invite_code = invite_code_line[0].split(":")[1].strip()
                logging.info(f"Found invite code: {invite_code}")
                
                # Extract full name from subject
                name_part = subject.split(":")[1].strip()
                last_name, first_name = name_part.split(", ")
                full_name = f"{first_name} {last_name}"
                logging.info(f"Extracted full name: {full_name}")
                
                return invite_code, full_name
            else:
                logging.warning("Invite code not found in the email body")
                return None, None
        except Exception as e:
            logging.error(f"Error extracting invite code and name: {e}")
            raise
    
    def delete_invite_email(self, email_id):
        """
        Deletes the invite email after successful processing.
        
        Parameters:
        - email_id (str): The ID of the email to delete.
        
        Raises:
        - Exception: If the email cannot be deleted.
        
        This method deletes an email from the inbox based on its ID after it has been 
        successfully processed to ensure it is not processed again.
        """
        try:
            self.mail.store(email_id, '+FLAGS', '\\Deleted')
            self.mail.expunge()
            logging.info(f"Successfully deleted invite email with ID: {email_id}")
        except Exception as e:
            logging.error(f"Failed to delete invite email: {str(e)}")
            raise
    
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

def log_response_info(response, is_splash_request=False):
    """
    Logs detailed information about an HTTP response.
    
    Parameters:
    - response (requests.Response): The HTTP response object to log.
    - is_splash_request (bool, optional): Indicates if the response is from a Splash request (default is False).
    
    This function logs the following details of an HTTP response:
    - Status code: The HTTP status code returned by the server.
    - Headers: The headers included in the HTTP response.
    - Cookies: Any cookies set by the server in the response.
    - Response body: The content of the response, with only the first 2000 characters logged for brevity.
    
    Additionally, if the response status code indicates an error (i.e., not 200 OK), the function attempts to 
    extract and log any error messages from the response body. If `is_splash_request` is True, it processes the 
    response as a JSON object, specifically looking for the 'html' field.
    
    Error Handling:
    - The function handles potential HTML parsing errors by using LexborHTMLParser to extract error messages 
      from the response body.
    - If a detailed error message is found within a `<div>` tag with the class `errortext`, it is logged as an error.
    
    The function logs all relevant information and includes separators to clearly distinguish the response 
    details in the logs.
    """
    logging.info("=== RESPONSE INFO ===")
    logging.info(f"Status Code: {response.status_code}")
    logging.info("Headers:")
    logging.info(json.dumps(dict(response.headers), indent=2))
    logging.info("Cookies:")
    logging.info(json.dumps(dict(response.cookies), indent=2))
    logging.info("Response Body:")
    if is_splash_request:
        result = response.json()
        text = result.get('html', None)
        logging.info(text[:2000])
    else:
        logging.info(response.text[:2000])  # Log first 2000 characters of response
    
    # Try to extract more detailed error information
    if response.status_code != 200:
        if is_splash_request:
            result = response.json()
            html = result.get('html', None)
            if html:
                parser = LexborHTMLParser(html)
            else:
                return None
        else:
            parser = LexborHTMLParser(response.text)
        
        # Extract error message
        error_divs = parser.css('div.errortext')
        if error_divs:
            error_msg = error_divs[0].text().strip()
            logging.error(f"Detailed error message: {error_msg}")
    
    logging.info("=====================")

def fetch_invite_code_and_name():
    """
    Retrieves invite codes and associated names from emails.
    
    Returns:
    - dict: A dictionary where the keys are invite codes and the values are lists containing 
            the full name associated with the invite and the email ID, i.e., {invite_code: [full_name, email_id]}.
            Returns an empty dictionary if no invites are found.
    
    This function connects to an email server using the `MailBox` class, searches for emails containing specific 
    subject lines that indicate an invite, and extracts the invite codes and user names from these emails.
    
    The process includes:
    - Connecting to the email server and logging in.
    - Selecting the inbox for searching relevant emails.
    - Searching for emails within a specified number of days using a predefined search string.
    - If no emails are found, performing a broader search using an alternative search string.
    - Sorting the found email IDs in descending order to prioritize more recent emails.
    - Fetching the content of each email, extracting the invite code and full name, and storing this information.
    
    Error Handling:
    - Logs relevant information if no emails are found matching the criteria.
    - If the function cannot find any invite emails or if there are errors during the process, 
      it returns an empty dictionary.
    - The function logs each step of the process for transparency and debugging purposes.

    Usage:
    - The function is used to automate the retrieval of invite codes from a set of emails, 
      which can be further processed as needed.
    """

    logging.info("Starting to fetch invite code and name")
    # Initialize an empty dictionary to store invite codes and associated names.
    # Keys will be invite codes, and values will be lists containing the full name and email ID.
    invite_code_full_name_data = {}
    try:
        # Create a MailBox instance to connect to the email server using provided credentials.
        # EMAIL0_USERNAME, EMAIL0_PASSWORD, and MAILURL0 should be predefined constants with email credentials and server URL.
        with MailBox(EMAIL0_USERNAME, EMAIL0_PASSWORD, EMAILURL0) as mailbox:
            # Access the inbox of the email account.
            mailbox.get_inbox()

            # Search for emails within the specified number of days MAIL_SEARCH_DAYS_VALUE that contain 
            # the text specified by MAIL_SEARCH_STRING. This string should relate to the invite emails' subject or content.
            invite_email_ids = mailbox.search_mail_using_date_text_value(MAIL_SEARCH_DAYS_VALUE, MAIL_SEARCH_STRING)

            # If no emails are found with the initial search criteria, perform a broader search with an alternative search string.
            if not invite_email_ids:
                # Try using broader search terms
                invite_email_ids = mailbox.search_mail_using_date_text_value(MAIL_SEARCH_DAYS_VALUE, MAIL_BROADER_SEARCH_STRING)
            
            # Check if any emails were found with the broader search criteria.
            if not invite_email_ids == None and not invite_email_ids == []:
                # Sort the found email IDs in descending order to prioritize more recent emails.
                invite_email_ids = mailbox.sort_email_ids(email_ids = invite_email_ids)
            else:
                # If no emails are found after the broader search, log this information and return an empty dictionary.
                logging.info("No invite found in any emails")
                return None

            for email_id in invite_email_ids:
                # Fetch the content of the email using the email ID.
                msg_data = mailbox.fetch_email(email_id)
                # If the email content is successfully retrieved, process it to extract invite code and full name.
                if msg_data:
                    invite_code, full_name = mailbox.process_email(msg_data)
                    # If both invite code and full name are successfully extracted, store them in the dictionary.
                    if invite_code and full_name:
                        print(f"Invite Code: {invite_code}, Full Name: {full_name}")
                        invite_code_full_name_data[invite_code] = [full_name, email_id]
            # Return the dictionary containing invite codes and associated names.
            return invite_code_full_name_data

    except Exception as e:
        logging.error(f"An error occurred while fetching invite: {str(e)}")
        return None


def navigate_enter_code_accept_invite(session, invitation_code=None, email_id=None, lua_script=None):
    """
    Navigates to the Pending Contact page on the Corrlinks website, enters an invitation code, 
    and attempts to accept the invite.

    Parameters:
    - session (requests.Session): The session object used to maintain and manage cookies and headers across requests.
    - invitation_code (str, optional): The invite code to be entered into the designated input box on the web page.
    - email_id (str, optional): The ID of the email containing the invitation code, used to delete the email after processing.
    - lua_script (str, optional): The Lua script used by the Splash service to render the page and interact with its elements.

    Returns:
    - dict: The JSON response from the Splash service if successful, containing the HTML content, 
            processing status, and other data.
    - None: If the function fails to process the invitation code after the maximum number of retries.

    This function performs the following steps:
    1. **Navigates to the Pending Contact Page**: It initiates a POST request to the Splash service with parameters 
       necessary for rendering and interacting with the Corrlinks website.
    2. **Session Validation**: Checks if the session is still valid by analyzing the response from the Splash service.
    3. **Form Submission and Invite Acceptance**: It attempts to enter the invitation code, submit the form, 
       and check for the presence of specific elements on the rendered page that indicate a successful submission.
    4. **Error Handling and Retries**: If the request fails, it retries up to a predefined number of times (`MAX_ACCEPT_INVITE_RETRIES`).
    5. **Email Deletion**: If the invitation code is processed successfully, it connects to the email server, 
       selects the inbox, and deletes the processed email.

    Logging:
    - Logs the session cookies before navigation to assist in debugging issues related to session management.
    - Logs detailed request and response information, including the response status, HTML content, 
      and error messages if the request fails.

    Usage:
    - This function is used to automate the acceptance of invitation codes on the Corrlinks website, 
      with detailed logging and error handling to ensure reliability in various network or site conditions.
    - The function's retry mechanism ensures multiple attempts to process the invitation code, 
      increasing the chances of success even if the initial request fails.
    """

    # Log the start of the navigation process and the session cookies for debugging.
    logging.info("Navigating to Pending Contact page")
    logging.info(f"Session cookies before navigation: {dict(session.cookies)}")

    # Convert the cookies from the `requests` format to the format required by Splash.
    # This prepares the cookies for use in the Splash request.
    splash_cookies = []
    splash_cookies = convert_cookies_to_splash_format(splash_cookies=splash_cookies, cookies=session.cookies)

    # Prepare the cookies as a header string to be included in the request.
    # This string is a semi-colon separated list of key-value pairs representing cookies.
    header_cookies = "; ".join([f"{key}={value}" for key, value in session.cookies.items()])

    # Define custom headers to be sent with the request to Splash.
    headers = HEADERS_FOR_ACCEPT_INVITE

    # Set up the parameters for the POST request to the Splash service.
    # These parameters include:
    # - Lua script to be executed by Splash
    # - URL of the page to navigate to
    # - Formatted cookies and custom headers
    # - IDs for HTML elements and the invitation code to be processed
    params = {
        'lua_source' : lua_script,
        'url' : CONTACT_URL,
        'splash_cookies' : splash_cookies,
        'cookies' : header_cookies,
        'headers' : headers,
        'invite_code_box_id' : INVITATION_CODE_BOX_ID,
        'invitation_code' : invitation_code,
        'person_in_custody_information_div_id' : PERSON_IN_CUSTODY_INFORMATION_DIV_ID,
        'invitation_code_go_button_id' : INVITATION_CODE_GO_BUTTON_ID,
        'invitation_accept_button_id' : INVITATION_ACCEPT_BUTTON_ID,
        'record_not_found_span_id' : RECORD_NOT_FOUND_SPAN_ID
    }
    max_retries = MAX_ACCEPT_INVITE_RETRIES

    for retry_number in range(max_retries):
        # Send a POST request to the Splash service with the specified parameters.
        # The Splash service renders the page and executes the Lua script provided.
        response = session.post(SPLASH_URL, json=params)
        result = response.json()

        # Retrieve the HTML content from the response if available.
        # This HTML content can be useful for debugging or further processing.
        page_html = result.get('html', None)
        if not page_html == None:
            # Log detailed response information for analysis.
            # This includes status codes, HTML content, and any other relevant details.
            log_response_info(response, is_splash_request=True)

        
        # Check if the invitation code was successfully processed.
        # The `is_processed` flag indicates whether the code was handled correctly.
        is_processed = result.get('is_processed', None)
        if is_processed:
            # If the invitation code was processed, connect to the email server.
            # Use the `MailBox` class to manage email operations.
            with MailBox(EMAIL0_USERNAME, EMAIL0_PASSWORD, EMAILURL0) as mailbox:
                mailbox.get_inbox()
                # Delete the email containing the invitation code to avoid reprocessing.
                mailbox.delete_invite_email(email_id=email_id)

        # Check if the expected HTML elements were found in the response.
        # This helps in verifying if the form submission was successful.
        element_found = result.get('element_found')
        if element_found:
            # Log success messages and additional details from the result.
            # This provides insights into the processing outcome and any extra messages.
            logging.info(f'Messages = {result['message']}\n. Extra Messages = {result['extra_messages']}')
            return result
        else:
            # If the request failed, log the failure and retry if necessary.
            # Save the screenshot if available to help with debugging.
            logging.info(f'Request failed for request number {retry_number +1}. Retrying ......')
            logging.error(f'Error Message = {result['error_message']}\n. Extra Messages = {result['extra_messages']}')

            # Break the loop if the invitation code was processed successfully.
            if is_processed:
                break
    
    # If all retry attempts fail, log an error message indicating the failure.
    # This provides a clear indication that the function did not succeed after multiple attempts.
    logging.error(f'Something went wrong in navigate_enter_code_accept_invite function. Check the logs above for more details.\n')
    return None
            

def process_invitation():
    """
    Processes an invitation from start to finish, handling the entire workflow from fetching 
    the invitation code to accepting the invitation on Corrlinks.

    Returns:
    - dict: A dictionary containing the results of processing each invitation code, with the invitation 
            code as the key and the result message or status as the value.
            - If successful, the value includes a success message and any additional information returned by the server.
            - If unsuccessful, the value will be `None`.

    This function orchestrates the invitation processing in several key steps:
    1. **Fetching Invitation Codes**:
        - Calls `fetch_invite_code_and_name()` to retrieve a dictionary of invitation codes, email IDs, and associated names.
        - If no invitation codes are found or if an error occurs during fetching, it logs an error and returns `False`.
    
    2. **Logging into Corrlinks**:
        - Initiates a session by calling `login_to_corrlinks()`.
        - If the login fails, the function logs an error and returns `False`.
        - Logs the session cookies after a successful login for debugging purposes.

    3. **Loading the Lua Script**:
        - Reads and loads a Lua script from a file, which is used by the Splash service to navigate and interact with the Corrlinks web page.

    4. **Processing Each Invitation Code**:
        - Iterates through each invitation code fetched earlier.
        - Calls `navigate_enter_code_accept_invite()` to submit the invitation code, handle the web page interaction, and accept the invitation.
        - Captures the response for each invite code:
            - If successful, the response includes a success message, which is logged and added to the `response_dict`.
            - If unsuccessful or if the request fails, logs the failure and stores `None` in `response_dict` for that code.

    5. **Returning the Results**:
        - Returns `response_dict`, which contains the processing results for each invitation code. 
          This allows the caller to check which invitations were successfully processed and which were not.

    Usage:
    - This function is designed to automate the process of handling invitations on Corrlinks, 
      including logging in, navigating to the relevant page, submitting the invitation code, and 
      accepting the invitation. It ensures that each step is logged and that errors are appropriately handled.
    - The function returns a dictionary that can be used to verify the outcome of each invitation code processed, 
      providing both success messages and error states.
    """

    # Step 1: Fetch invitation codes and associated email addresses.
    # This function should return a dictionary where keys are invitation codes and values are tuples (or lists)
    # with email addresses and possibly other relevant data.
    invite_codes_dict = fetch_invite_code_and_name()
    if not invite_codes_dict or invite_codes_dict == {}:
        logging.error("Failed to fetch invite code")
        return False

    # Step 2: Log in to Corrlinks to get a session.
    # This function should return a session object that includes cookies for authenticated requests.
    session = login_to_corrlinks()
    if not session:
        # If login fails, log an error and exit the function with a failure indicator.
        logging.error("Failed to login to Corrlinks")
        return False

    # Log the session cookies for debugging purposes.
    logging.info(f"Session cookies after login: {dict(session.cookies)}")

    # Step 3: Read the Lua script from a file.
    # The Lua script is necessary for interacting with the web application via Splash (a headless browser).
    with open('utils/lua_scripts/navigate_enter_code_accept_invite.lua', 'r') as file:
        lua_script = file.read()

    # Dictionary to store the results of processing each invitation code.
    response_dict = {}
    # Step 4: Iterate over each invitation code and associated email address.
    for invite_code, value in invite_codes_dict.items():
        email_id = value[1]

        # Call the function to navigate, enter the invitation code, and accept the invitation.
        # This function will interact with the web application using the provided session and Lua script.
        response_value = navigate_enter_code_accept_invite(session=session, invitation_code=invite_code, email_id=email_id, lua_script=lua_script)
        
        # Check if the response is not None and update the message accordingly.
        if not response_value == None:
            message = f'Invite code {invite_code} processed successfuly.'
            message = message + response_value.get('message')
            logging.info(f'Output for {invite_code} = {response_value}')
            response_dict[invite_code] = message
        else:
            # Log the response for debugging if the result is None.
            logging.info(f'Output for {invite_code} = {response_value}')
            response_dict[invite_code] = response_value

    # Step 5: Return the dictionary containing the results for each invitation code.
    # The dictionary will have invitation codes as keys and result messages as values.
    return response_dict


if __name__ == "__main__":
    result = process_invitation()
    print("Invitation processing result:", result)