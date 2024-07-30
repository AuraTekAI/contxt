import pyautogui
import pyperclip
import subprocess
import time
import logging
from variables import *

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_email_handler(db_ops):
    db_ops.set_email_callback(process_emails)

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
    
        # Click login button
        for _ in range(2):
            pyautogui.press('tab')
        pyautogui.press('enter')
        pyautogui.press('enter')
        time.sleep(3)  # Wait for login to complete

        current_url = check_current_url()
        if current_url == DEFAULT_URL:
            logging.info("Successfully logged in and reached Default.aspx")
            return True
        else:
            logging.warning(f"Login attempt {attempt + 1} failed. Current URL: {current_url}")

    logging.error("Failed to log in after maximum attempts")
    return False

def navigate_to_reply(url):
    logging.info(f"Navigating to reply page: {url}")
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(0.5)
    pyautogui.write(url)
    pyautogui.press('enter')
    time.sleep(5)
    
def send_reply(message):
    logging.info("Sending reply")
    pyautogui.write(message)
    time.sleep(2)
    
    # Navigate to send button
    for _ in range(3):
        pyautogui.press('tab')
    pyautogui.press('enter')
    time.sleep(3)  # Wait for message to send
    
    return verify_message_sent()

def verify_message_sent():
    logging.info("Verifying message was sent successfully")
    
    # Wait a moment for the page to load after sending
    time.sleep(3)
    
    # Get the current URL
    current_url = check_current_url()
    
    if current_url == MESSAGE_PROCESSED:
        logging.info("Message sent successfully. Correct URL confirmed.")
        return True
    else:
        logging.error(f"Message may not have been sent. Unexpected URL: {current_url}")
        return False

def close_browser():
    logging.info("Closing the browser")
    pyautogui.hotkey('alt', 'f4')
    time.sleep(2)

def process_emails(user_id, subject, body):
    try:
        open_firefox()
        if not login_to_corrlinks():
            logging.error("Failed to log in. Exiting...")
            return False

        # Construct the reply URL (you may need to modify this based on your system)
        reply_url = REPLY_URL_BASE.format(user_id=user_id)

        navigate_to_reply(reply_url)
        if send_reply(f"Subject: {subject}\n\n{body}"):
            logging.info(f"Successfully sent email to user {user_id}")
            close_browser()
            return True
        else:
            logging.error(f"Failed to send email to user {user_id}")
            close_browser()
            return False

    except Exception as e:
        logging.error(f"An error occurred while processing email: {str(e)}")
        close_browser()
        return False

def main():
    user_id = "15372010"
    subject = "Test Subject"
    body = "This is a test email body."
    result = process_emails(user_id, subject, body)
    print(f"Email sent successfully: {result}")

if __name__ == "__main__":
    main()