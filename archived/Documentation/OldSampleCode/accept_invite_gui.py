import pyautogui
import pyperclip
import subprocess
import logging
import time
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from variables import *
from db_ops import get_database_connection, close_database_resources

# Set up logging
logging.basicConfig(filename='invite_error.log', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_all_invites():
    logging.info("Starting to fetch all invite codes and names")
    invites = []
    try:
        mail = imaplib.IMAP4_SSL(EMAILURL0)
        logging.info(f"Connected to: {EMAILURL0}")
        
        mail.login(EMAIL0_USERNAME, EMAIL0_PASSWORD)
        logging.info(f"Logged in with username: {EMAIL0_USERNAME}")
        
        mail.select("inbox")
        logging.info("Selected inbox")
        
        date_since = (datetime.now() - timedelta(days=10)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SUBJECT "Person in Custody:" SINCE "{date_since}")')
        invite_email_ids = messages[0].split()
        logging.info(f"Search status: {status}, Number of invite messages found: {len(invite_email_ids)}")
        
        if not invite_email_ids:
            logging.info("No emails found with exact subject. Trying a broader search.")
            status, messages = mail.search(None, f'(SUBJECT "Custody" SINCE "{date_since}")')
            invite_email_ids = messages[0].split()
            logging.info(f"Broader search status: {status}, Number of potential invite messages found: {len(invite_email_ids)}")
        
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
                        
                        invite_code_line = [line for line in body.split('\n') if "Identification Code:" in line]
                        if invite_code_line:
                            invite_code = invite_code_line[0].split(":")[1].strip()
                            logging.info(f"Found invite code: {invite_code}")
                            
                            name_part = subject.split(":")[1].strip()
                            last_name, first_name = name_part.split(", ")
                            full_name = f"{first_name} {last_name}"
                            logging.info(f"Extracted full name: {full_name}")
                            
                            invites.append((invite_code, email_id, full_name, subject))
                    else:
                        logging.info(f"Email subject does not match exactly: {subject}")
        
        if not invites:
            logging.info("No invites found in any emails")
        else:
            logging.info(f"Found {len(invites)} invites")
        return invites
    except Exception as e:
        logging.error(f"An error occurred while fetching invites: {str(e)}")
        return []
    finally:
        try:
            mail.logout()
            logging.info("Logged out from mail server")
        except:
            pass

def open_firefox():
    subprocess.Popen(["C:\\Program Files\\Mozilla Firefox\\firefox.exe"])
    time.sleep(3)  # Wait for Firefox to open

def check_current_url():
    logging.info("Checking current URL")
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.5)
    return pyperclip.paste()

def login_to_corrlinks(max_attempts=3):
    for attempt in range(max_attempts):
        logging.info(f"Logging into Corrlinks (Attempt {attempt + 1}/{max_attempts})")
        pyautogui.write(LOGIN_URL)
        pyautogui.press('enter')
        time.sleep(3)  # Wait for page to load

        # Enter username
        pyautogui.write(USERNAME)
        pyautogui.press('tab')
    
        # Enter password
        pyautogui.hotkey('ctrl', 'a')  # Select all text in the address bar
        pyautogui.press('delete')  # Clear the selected text
        pyautogui.write(PASSWORD)
        time.sleep(0.5)
    
        # Click login button
        for _ in range(2):
            pyautogui.press('tab')
        pyautogui.press('enter')
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(3)  # Wait for login to complete

        current_url = check_current_url()
        if current_url == CONTACT_URL:
            logging.info("Successfully logged in and reached Default.aspx")
            return True
        else:
            logging.warning(f"Login attempt {attempt + 1} failed. Current URL: {current_url}")

    logging.error("Failed to log in after maximum attempts")
    return False

def navigate_to_contact_page():
    logging.info("Navigating to Pending Contact page")
    pyautogui.hotkey('ctrl', 'l')  # Focus on address bar
    time.sleep(0.5)
    pyautogui.write(CONTACT_URL)
    pyautogui.press('enter')
    time.sleep(3)  # Wait for page load
    
    # Verify we're on the correct page
    current_url = check_current_url()
    
    if CONTACT_URL not in current_url:
        logging.error(f"Failed to navigate to Contact page. Current URL: {current_url}")
        return False
    
    logging.info("Successfully navigated to Contact page")
    return True

def process_invite(invite_code, full_name, original_subject, is_last_invite):
    try:
        logging.info(f"Processing invite for {full_name}")
        
        # Navigate to the contact page
        if not navigate_to_contact_page():
            return False

        # Navigate to the invite code input field
        for _ in range(4):
            pyautogui.press('tab')
        time.sleep(0.5)
        
        # Paste the invite code
        pyperclip.copy(invite_code)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        
        # Navigate to and click the "go" button
        pyautogui.press('tab')
        pyautogui.press('enter')
        time.sleep(2)  # Wait for the dynamic page to load
        
        # Check if the invite code was accepted
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        page_content = pyperclip.paste()
        
        if "invalid identification code" in page_content.lower():
            logging.error(f"Invalid invite code for {full_name}")
            return False
        
        # Extract the name from the page content
        name_line = [line for line in page_content.split('\n') if "Name:" in line]
        if not name_line:
            logging.error("Could not find name line in page content")
            return False
        
        displayed_name = name_line[0].split("Name:")[1].strip()
        
        # Extract the name from the original subject (removing "Person in Custody: ")
        expected_name = original_subject.replace("Person in Custody:", "").strip()
        
        # Normalize both names by removing spaces around commas
        expected_name_normalized = ','.join(part.strip() for part in expected_name.split(','))
        displayed_name_normalized = ','.join(part.strip() for part in displayed_name.split(','))
        
        if expected_name_normalized.lower() != displayed_name_normalized.lower():
            logging.error(f"Name mismatch. Expected: {expected_name}, Found: {displayed_name}")
            return False
        
        logging.info(f"Name matched successfully: {displayed_name}")
        
        # Navigate to the accept button
        for _ in range(7):
            pyautogui.press('tab')
        
        # Accept the invite
        pyautogui.press('enter')
        time.sleep(3)  # Wait for acceptance to process
        
        # Verify the invite was accepted
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        result_text = pyperclip.paste().lower()
        
        if is_last_invite:
            if "your identification code has been approved" in result_text:
                logging.info(f"Successfully accepted last invite for {displayed_name}")
                return True
            else:
                logging.error(f"Failed to verify last invite acceptance for {displayed_name}")
                return False
        else:
            if "new contact request" in result_text:
                logging.info(f"Successfully accepted invite for {displayed_name}")
                return True
            else:
                logging.error(f"Failed to verify invite acceptance for {displayed_name}")
                return False
        
    except Exception as e:
        logging.error(f"Error processing invite for {full_name}: {str(e)}")
        return False

def delete_invite_email(email_id):
    """
    Deletes the specified email from the inbox.
    """
    logging.info(f"Attempting to delete email with ID: {email_id}")
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(EMAILURL0)
        # Login to your account
        mail.login(EMAIL0_USERNAME, EMAIL0_PASSWORD)
        # Select the mailbox you want to delete from
        mail.select("inbox")
        
        # Mark the email as deleted
        mail.store(email_id, '+FLAGS', '\\Deleted')
        
        # Permanently remove emails marked for deletion
        mail.expunge()
        
        logging.info(f"Successfully deleted invite email with ID: {email_id}")
        return True
    except Exception as e:
        logging.error(f"Failed to delete invite email: {str(e)}")
        return False
    finally:
        try:
            mail.logout()
        except:
            pass

def delete_processed_emails(email_ids):
    logging.info(f"Starting post-processing: Deleting {len(email_ids)} successfully processed emails")
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(EMAILURL0)
        # Login to your account
        mail.login(EMAIL0_USERNAME, EMAIL0_PASSWORD)
        # Select the mailbox you want to delete from
        mail.select("inbox")
        
        for email_id in email_ids:
            try:
                # Mark the email as deleted
                mail.store(email_id, '+FLAGS', '\\Deleted')
                logging.info(f"Marked email ID {email_id} for deletion")
            except Exception as e:
                logging.error(f"Failed to mark email ID {email_id} for deletion: {str(e)}")
        
        # Permanently remove emails marked for deletion
        mail.expunge()
        logging.info("Expunged marked emails")
        
    except Exception as e:
        logging.error(f"Error during post-processing email deletion: {str(e)}")
    finally:
        try:
            mail.logout()
            logging.info("Logged out from mail server after post-processing")
        except:
            pass

def main():
    logging.info("Starting invite processing script")
    successfully_processed = []

    # Fetch all invites
    invites = fetch_all_invites()

    if not invites:
        logging.info("No invites to process. Exiting script.")
        return

    logging.info(f"Found {len(invites)} invites to process.")

    # Open Firefox and log in only if we have invites to process
    open_firefox()
    if not login_to_corrlinks():
        logging.error("Failed to log in. Exiting...")
        return

    # Process each invite
    for index, (invite_code, email_id, full_name, original_subject) in enumerate(invites):
        is_last_invite = (index == len(invites) - 1)
        if process_invite(invite_code, full_name, original_subject, is_last_invite):
            successfully_processed.append(email_id)
            logging.info(f"Successfully processed invite for {full_name}")
        else:
            logging.error(f"Failed to process invite for {full_name}.")
        
        time.sleep(2)  # Short delay between processing invites

    logging.info("Finished processing all invites.")
    
    # Post-processing: Delete successfully processed emails
    if successfully_processed:
        delete_processed_emails(successfully_processed)

    # Keep the browser open for future use

if __name__ == "__main__":
    main()