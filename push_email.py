# push_email.py

import logging
import json
import datetime

from login import login_to_corrlinks
from variables import MAX_EMAIL_REPLY_RETRIES, HEADERS_FOR_PUSH_EMAIL_REQUEST, LUA_SCRIPT, SPLASH_URL


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

def log_response_info(response, is_splash_response=False, retry_number=0):
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
    
    # Save the full HTML content to a file for inspection
    if is_splash_response:
        json_response = response.json()
        html_content = json_response.get('html')
        logging.info(f"Response Body: {response.text[:1000]}")
        if not html_content == None:
            with open(f"response_content_{response.status_code}_try{retry_number}.html", "w", encoding="utf-8") as f:
                f.write(html_content)
        else:
            logging.error(f"Empty HTML page returned. {response.url} {response.status_code}")
    else:
        logging.info(f"Response Body: {response.text[:1000]}")
        with open(f"response_content_{response.status_code}_try{retry_number}.html", "w", encoding="utf-8") as f:
            f.write(response.text)
    logging.info(f"=====================")

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
    

def send_email_reply(session, message_content, message_id, session_state):
    """
    Sends an email reply through the Corrlinks system.
    Parameters:
    - session (requests.Session): The session object for making requests
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
    
    """
    Setting up lua_script that needs to run on the splash browser window.
    Also settings headers and cookies, which are later used in splash.
    """
    lua_script = LUA_SCRIPT
    headers = HEADERS_FOR_PUSH_EMAIL_REQUEST
    cookies = session_state['cookies']

    """
    Here converting the cookies to a format that is accpeted by the splash browser
    Return False if an error occurs during conversion of the cookie format.
    """
    splash_cookies = []
    splash_cookies = convert_cookies_to_splash_format(splash_cookies=splash_cookies, cookies=cookies)
    if splash_cookies == False:
        logging.error(f'Error occured while converting cookies to splash browser format. \
        This is what was returned by the |convert_cookies_to_splash_format| function. {splash_cookies}')
        return False

    """
    This function converts cookies into a string format for use in request headers.
    In Splash, cookies are handled as key-value pairs, 
    but when used in request headers, they must be formatted as a single string.
    """
    cookie_header = "; ".join([f"{key}={value}" for key, value in cookies.items()])

    # Setting up all the required parameters for the request to the splash service.
    params = {
        'lua_source': lua_script,
        'message_content': message_content,
        'reply_url': reply_url,
        'headers' : headers,
        'cookies' : cookie_header,
        'splash_cookies' : splash_cookies
    }

    """
    This is a simple retry mechanism for the email reply request.
    It is implemented to handle potential throttling by the server we're sending requests to.
    The mechanism ensures that multiple attempts are made before giving up.
    """
    result = None
    request_success = False
    for retry_number in range(MAX_EMAIL_REPLY_RETRIES):
        response = session.post(SPLASH_URL, json=params)
        result = response.json()

        log_response_info(response=response, is_splash_response=True, retry_number=retry_number + 1)
        if response.status_code == 200 and not result['text_box_message'] == 'Text box not found':
            request_success = True
            break
    
    # if the request was successful, log the relevant messages and return True.
    if response.status_code == 200 and request_success:
        element_found = result.get('element_found')
        if element_found:
            logging.info('Reply sent successfully.')
            logging.info('----------------------------------')
            return True

    """
    if we are here it means something went wrong in the above code.
    Log the relevant messages and return False.
    """
    logging.error(f'Something went wrong in send_reply_email.')
    logging.error('----------------------------------')
    return False


def run_push_email():
    """
    Runs the push email process.
    Returns:
    - str: A message indicating the result of the process

    This function orchestrates the process of sending a test reply email.
    It logs into Corrlinks, navigates to the reply page, sends the email reply,
    and handles the response. It's designed for testing and logging purposes.
    """

    # TODO Get these from the database.
    message_id = "3728844321"
    message_content = "This is a test reply message. Please ignore these messages. Appologies for any inconvenience."
    
    session = login_to_corrlinks()
    if not session:
        logging.error("Failed to login to Corrlinks")
        return "Failed to login to Corrlinks"

    # Capture the session state right after login
    session_state = capture_session_state(session)

    """
    This part is responsible for replying to the message. First step is navigation to the reply page.
    Second step is to enter the message in the textbox.
    Last step is to send the reply to the sender of the message.
    All relevant logging has been moved inside the send_email_reply function.
    """
    success = send_email_reply(session=session, message_content=message_content, message_id=message_id, session_state=session_state)
    if success:
        logging.info("Email reply sent successfully")
        return "Email reply sent successfully. Check push_email_interaction.log for details."
    else:
        logging.error("Failed to send email reply")
        return "Failed to send email reply. Check push_email_interaction.log for details."

if __name__ == "__main__":
    print(run_push_email())