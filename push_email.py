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