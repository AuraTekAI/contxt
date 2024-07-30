# data_logger.py

import logging
from login import login_to_corrlinks
from variables import CONTACT_URL
import time
from bs4 import BeautifulSoup
import json

# Set up logging
logging.basicConfig(filename='corrlinks_interaction.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def log_request_info(url, method, headers, data=None, params=None, cookies=None):
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
    logging.info("=== RESPONSE INFO ===")
    logging.info(f"Status Code: {response.status_code}")
    logging.info("Headers:")
    logging.info(json.dumps(dict(response.headers), indent=2))
    logging.info("Cookies:")
    logging.info(json.dumps(dict(response.cookies), indent=2))
    logging.info("Response Body:")
    logging.info(response.text[:2000])  # Log first 2000 characters of response
    logging.info("=====================")

def extract_form_data(html):
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
    logging.info("Navigating to Pending Contact page")
    response = session.get(CONTACT_URL)
    log_request_info(CONTACT_URL, "GET", dict(response.request.headers), 
                     cookies=session.cookies)
    log_response_info(response)
    
    form_data = extract_form_data(response.text)
    
    return response, form_data

def enter_invite_code(session, form_data, invite_code):
    logging.info(f"Entering invite code: {invite_code}")
    
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
    log_response_info(response)
    
    return response

def accept_invitation(session, form_data, invite_code):
    logging.info("Accepting invitation")
    
    # Update form data with all fields from the previous response
    form_data.update({
        '__EVENTTARGET': 'ctl00$mainContentPlaceHolder$PendingContactUC1$addInmateButton',
        'ctl00$mainContentPlaceHolder$PendingContactUC1$InmateNumberTextBox': invite_code,
        'DES_Group': 'SEARCHRESULTGROUP',
        'ctl00$topScriptManager': 'ctl00$topUpdatePanel|ctl00$mainContentPlaceHolder$PendingContactUC1$addInmateButton',
        '__ASYNCPOST': 'true'
    })
    
    headers = session.headers.copy()
    headers.update({
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-MicrosoftAjax': 'Delta=true',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': CONTACT_URL,
        'Origin': 'https://www.corrlinks.com',
        'Accept': '*/*'
    })
    
    log_request_info(CONTACT_URL, "POST", headers, data=form_data)
    response = session.post(CONTACT_URL, data=form_data, headers=headers, allow_redirects=True)
    log_response_info(response)
    
    if response.status_code == 200:
        if "Contact request accepted" in response.text:  # Replace with actual success message
            logging.info("Invitation accepted successfully")
            return True
        elif "You have 1 new contact request" in response.text:
            logging.warning("Invitation might not have been accepted. Contact request still showing.")
            return False
        else:
            logging.warning("Unexpected response content. Manual verification needed.")
            return False
    else:
        logging.error(f"Error accepting invitation: Status {response.status_code}")
        logging.error(f"Response content: {response.text[:500]}")
        return False

def run_data_logger():
    invite_code = "6F876NMY"  # Hardcoded for testing
    
    session = login_to_corrlinks()
    if not session:
        logging.error("Failed to login to Corrlinks")
        return "Failed to login to Corrlinks"

    response, form_data = navigate_to_pending_contact(session)
    if response.status_code != 200:
        logging.error(f"Failed to navigate to Pending Contact page. Status code: {response.status_code}")
        return f"Failed to navigate to Pending Contact page. Status code: {response.status_code}"

    time.sleep(2)

    response = enter_invite_code(session, form_data, invite_code)
    if response.status_code != 200:
        logging.error(f"Failed to enter invite code. Status code: {response.status_code}")
        return f"Failed to enter invite code. Status code: {response.status_code}"

    time.sleep(2)

    response = accept_invitation(session, form_data, invite_code)  # Pass invite_code here
    if response.status_code != 200:
        logging.error(f"Failed to accept invitation. Status code: {response.status_code}")
        return f"Failed to accept invitation. Status code: {response.status_code}"

    logging.info("Data logging process completed successfully")
    return "Data logging process completed successfully. Check corrlinks_interaction.log for details."

if __name__ == "__main__":
    print(run_data_logger())