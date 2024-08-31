
from accounts.mail_service import MailBox
from accounts.utils import get_email_password_url, MAP_EMAIL_URL_TO_EMAIL_SEARCH_STRINGS
from accounts.login_service import SessionManager
from contxt.utils.helper_functions import get_lua_script_absolute_path, save_screenshots_to_local

from django.core.management.base import BaseCommand, CommandParser

from process_emails.utils import convert_cookies_to_splash_format

from selectolax.lexbor import LexborHTMLParser
from django.conf import settings

import logging
import json
import sys

logger = logging.getLogger('accpet_invite')

class Command(BaseCommand):
    help = 'Process invitation codes from emails and accept them in Corrlinks.'

    def add_arguments(self, parser):
        parser.add_argument('--bot_id', type=int)

    def handle(self, *args, **options):
        bot_id = options.get('bot_id')

        logger.info(f'Accept invite got bot id = {bot_id} ')

        result = process_invitation(bot_id=bot_id)
        logger.info(f"Invitation processing result for bot {bot_id}: {result}")

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
    logger.info(f"=== REQUEST INFO ({method}) ===")
    logger.info(f"URL: {url}")
    logger.info("Headers:")
    logger.info(json.dumps(dict(headers), indent=2))
    if data:
        logger.info("Form Data:")
        logger.info(json.dumps(data, indent=2))
    if params:
        logger.info("URL Parameters:")
        logger.info(json.dumps(params, indent=2))
    if cookies:
        logger.info("Cookies:")
        logger.info(json.dumps(dict(cookies), indent=2))
    logger.info("====================")

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
    logger.info("=== RESPONSE INFO ===")
    logger.info(f"Status Code: {response.status_code}")
    logger.info("Headers:")
    logger.info(json.dumps(dict(response.headers), indent=2))
    logger.info("Cookies:")
    logger.info(json.dumps(dict(response.cookies), indent=2))
    logger.info("Response Body:")
    if is_splash_request:
        result = response.json()
        text = result.get('html', None)
        logger.info(text[:2000])
    else:
        logger.info(response.text[:2000])  # Log first 2000 characters of response

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
            logger.error(f"Detailed error message: {error_msg}")

    logger.info("=====================")

def fetch_invite_code_and_name(bot_id=None):
    """
    Fetches invitation codes and full names from recent emails.

    This function orchestrates the process of connecting to an email inbox, searching
    for specific emails, extracting invitation codes and full names, and deleting
    the processed emails. The function is designed to handle cases where the email
    content might not match the exact search criteria and includes broader search options.

    Returns:
    - dict: A dictionary where the keys are invitation codes (str) and the values are lists
      containing the full name (str) and email ID (str). If no valid emails are found,
      it returns None.

    Workflow:
    1. It logs the start of the fetching process.
    2. Retrieves user credentials and the email server URL.
    3. Connects to the mailbox using the `MailBox` class within a context manager (`with` statement),
       ensuring the mailbox is properly closed after operations.
    4. Selects the inbox and searches for emails matching the `MAIL_SEARCH_DAYS_VALUE` and `MAIL_SEARCH_STRING`
       criteria.
    5. If no emails are found, it broadens the search using `MAIL_BROADER_SEARCH_STRING`.
    6. Sorts the found email IDs in descending order to process the most recent emails first.
    7. Iterates over the sorted email IDs, fetching and processing each email to extract the invitation
       code and full name.
    8. If successful, stores the invite code, full name, and email ID in a dictionary.
    9. Returns the dictionary containing all found invite codes and names.

    Error Handling:
    - Logs and returns None if an error occurs during any of the steps.
    """
    logger.info(f"Starting to fetch invite code and name for bot {bot_id}")  # Log the start of the fetching process

    invite_code_full_name_data = {}  # Dictionary to store invite codes and associated full names

    try:
        # Retrieve email credentials and URL
        user_name, password, email_Url = get_email_password_url(bot_id=bot_id)

        if user_name is None and password is None and email_Url is None:
            return invite_code_full_name_data

        # Use the MailBox class within a context manager to ensure proper cleanup
        with MailBox(user_name, password, email_Url) as mailbox:
            # Select the inbox folder
            mailbox.get_inbox()

            search_string = MAP_EMAIL_URL_TO_EMAIL_SEARCH_STRINGS[email_Url]
            # Search for emails based on specific days and text criteria
            invite_email_ids = mailbox.search_mail_using_date_text_value(settings.MAIL_SEARCH_DAYS_VALUE, search_string[0])

            # If no emails are found with the primary search string, broaden the search
            if not invite_email_ids:
                invite_email_ids = mailbox.search_mail_using_date_text_value(settings.MAIL_SEARCH_DAYS_VALUE, search_string[1])

            # If emails are found, sort them by ID in descending order
            if invite_email_ids:
                invite_email_ids = mailbox.sort_email_ids(email_ids=invite_email_ids)
            else:
                # Log and exit if no invite emails are found
                logger.info(f"No invite found in any emails for bot = {bot_id}")
                return None

            # Iterate over the sorted email IDs and process each email
            for email_id in invite_email_ids:
                # Fetch the email data for the current email ID
                msg_data = mailbox.fetch_email(email_id)
                if msg_data:
                    # Process the email to extract the invite code and full name
                    invite_code, full_name = mailbox.process_email(msg_data)
                    if invite_code and full_name:
                        # Print the invite code and full name (could be changed to logging if necessary)
                        print(f"Invite Code: {invite_code}, Full Name: {full_name}")
                        # Store the extracted data in the dictionary
                        invite_code_full_name_data[invite_code] = [full_name, email_id]
            # Return the dictionary with invite codes and names
            return invite_code_full_name_data
    except Exception as e:
        # Log any errors that occur during the process
        logger.error(f"An error occurred while fetching invite for bot = {bot_id}: {str(e)}")
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
    logger.info("Navigating to Pending Contact page")
    logger.info(f"Session cookies before navigation: {dict(session.cookies)}")

    # Convert the cookies from the `requests` format to the format required by Splash.
    # This prepares the cookies for use in the Splash request.
    splash_cookies = []
    splash_cookies = convert_cookies_to_splash_format(splash_cookies=splash_cookies, cookies=session.cookies)

    # Prepare the cookies as a header string to be included in the request.
    # This string is a semi-colon separated list of key-value pairs representing cookies.
    header_cookies = "; ".join([f"{key}={value}" for key, value in session.cookies.items()])

    # Define custom headers to be sent with the request to Splash.
    headers = settings.HEADERS_FOR_ACCEPT_INVITE

    # Set up the parameters for the POST request to the Splash service.
    # These parameters include:
    # - Lua script to be executed by Splash
    # - URL of the page to navigate to
    # - Formatted cookies and custom headers
    # - IDs for HTML elements and the invitation code to be processed
    params = {
        'lua_source' : lua_script,
        'url' : settings.CONTACT_URL,
        'splash_cookies' : splash_cookies,
        'cookies' : header_cookies,
        'headers' : headers,
        'invite_code_box_id' : settings.INVITATION_CODE_BOX_ID,
        'invitation_code' : invitation_code,
        'person_in_custody_information_div_id' : settings.PERSON_IN_CUSTODY_INFORMATION_DIV_ID,
        'invitation_code_go_button_id' : settings.INVITATION_CODE_GO_BUTTON_ID,
        'invitation_accept_button_id' : settings.INVITATION_ACCEPT_BUTTON_ID,
        'record_not_found_span_id' : settings.RECORD_NOT_FOUND_SPAN_ID
    }
    max_retries = settings.MAX_ACCEPT_INVITE_RETRIES

    for retry_number in range(max_retries):
        # Send a POST request to the Splash service with the specified parameters.
        # The Splash service renders the page and executes the Lua script provided.
        response = session.post(settings.SPLASH_URL, json=params)
        result = response.json()

        if settings.TEST_MODE:
            """
            For saving screenshots to local for debugging,
            please make sure they have word screenshot in their key value.
            """
            save_screenshots_to_local(result=result, logger_name=logger.name)

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
            user_name, password, email_Url = get_email_password_url()
            # If the invitation code was processed, connect to the email server.
            # Use the `MailBox` class to manage email operations.
            with MailBox(user_name, password, email_Url) as mailbox:
                mailbox.get_inbox()
                # Delete the email containing the invitation code to avoid reprocessing.
                mailbox.delete_invite_email(email_id=email_id)

        # Check if the expected HTML elements were found in the response.
        # This helps in verifying if the form submission was successful.
        element_found = result.get('element_found')
        if element_found:
            # Log success messages and additional details from the result.
            # This provides insights into the processing outcome and any extra messages.
            logger.info(f'Messages = {result['message']}\n. Extra Messages = {result['extra_messages']}')
            return result
        else:
            # If the request failed, log the failure and retry if necessary.
            # Save the screenshot if available to help with debugging.
            logger.info(f'Request failed for request number {retry_number +1}. Retrying ......')
            logger.error(f'Error Message = {result['error_message']}\n. Extra Messages = {result['extra_messages']}')

            # Break the loop if the invitation code was processed successfully.
            if is_processed:
                break

    # If all retry attempts fail, log an error message indicating the failure.
    # This provides a clear indication that the function did not succeed after multiple attempts.
    logger.error(f'Something went wrong in navigate_enter_code_accept_invite function. Check the logs above for more details.\n')
    return None

def process_invitation(bot_id=None):
    """
    Manages the complete process of fetching invitation codes from emails, logging into Corrlinks,
    and submitting the codes to accept pending invitations.

    Returns:
    - dict: A dictionary containing the processing status for each invitation code. Each key is an invitation code,
            and its value is a message indicating whether the code was processed successfully or an error occurred.
    - bool: Returns `False` if there was a failure at any step in the process, such as fetching invitation codes or logging in.

    This function performs the following steps:
    1. **Fetch Invitation Codes and Corresponding Emails**:
       - Calls the `fetch_invite_code_and_name` function to retrieve a dictionary of invitation codes and email details.
       - If this step fails, logs an error and returns `False`.

    2. **Session Management**:
       - Obtains a session using the `SessionManager.get_session()` method, which handles the login to Corrlinks.
       - If session retrieval fails, logs an error and returns `False`.
       - Logs the session cookies for debugging purposes.

    3. **Load Lua Script**:
       - Loads the Lua script from the specified file path, which will be used to automate interactions with the Corrlinks website.

    4. **Process Each Invitation Code**:
       - Iterates over each invitation code fetched from the emails.
       - For each code, it calls `navigate_enter_code_accept_invite` to navigate to the Pending Contact page, enter the code, and accept the invite.
       - Logs detailed response information for each code, including success or failure messages.
       - If the invitation is processed successfully, it stores a success message in the `response_dict`.
       - If the function encounters an issue with a particular code, it logs the issue and stores the failure message in `response_dict`.

    5. **Return Processing Results**:
       - Returns the `response_dict`, which contains the processing status for each invitation code.
       - Each key in the dictionary represents an invitation code, and the value indicates whether it was successfully processed or not.
    """
    logger.info(f"Starting the invitation processing for bot = {bot_id}")
    invite_codes_dict = fetch_invite_code_and_name(bot_id=bot_id)
    if not invite_codes_dict or invite_codes_dict == {}:
        logger.info("No new invites found in mail. Check logs above this for more details.")
        return False

    session = SessionManager.get_session(bot_id=bot_id)
    if not session:
        logger.error(f"Failed to login to Corrlinks for bot = {bot_id}")
        return False

    logger.info(f"Session cookies after login: {dict(session.cookies)}")

    lua_script_path = get_lua_script_absolute_path(relative_path='lua_scripts/navigate_enter_code_accept_invite.lua')
    with open(lua_script_path, 'r') as file:
        lua_script = file.read()

    response_dict = {}
    for invite_code, value in invite_codes_dict.items():
        email_id = value[1]
        invite_code = invite_code
        logger.info(f"Starting navigating enter code for bot = {bot_id}")
        response_value = navigate_enter_code_accept_invite(session=session, invitation_code=invite_code, email_id=email_id, lua_script=lua_script)

        if not response_value == None:
            message = f'Invite code {invite_code} processed successfully.'
            message += response_value.get('message')
            logger.info(f'Output for {invite_code} = {response_value}')
            response_dict[invite_code] = message
        else:
            logger.info(f'Output for {invite_code} = {response_value}')
            response_dict[invite_code] = response_value
    logger.info(f"Ended navigating enter code for bot = {bot_id}")
    return response_dict
