
from accounts.login_service import SessionManager
from accounts.utils import get_or_create_user
from process_emails.utils import save_emails
from contxt.utils.constants import CURRENT_TASKS_RUN_BY_BOTS

from django.core.management.base import BaseCommand
from django.conf import settings

from selectolax.lexbor import LexborHTMLParser
from requests_toolbelt import MultipartEncoder

import re
import logging


HEADERS = settings.PULL_EMAIL_REQUEST_HEADERS
HEADERS['Referer'] = settings.INBOX_URL

class Command(BaseCommand):
    help = 'Process unread emails from the Corrlinks inbox'
    command_name = CURRENT_TASKS_RUN_BY_BOTS['pull_emails']

    def add_arguments(self, parser):
        parser.add_argument('--bot_id', type=int, help='The bot id for the bot executing tasks.')

    def handle(self, *args, **options):
        """
        Main command handler to process unread emails from the Corrlinks inbox.

        The command performs the following actions:
        1. Retrieves a session using the `SessionManager`.
        2. Fetches the inbox page and checks the response status.
        3. Parses the inbox page to retrieve `COMPRESSEDVIEWSTATE` and email rows.
        4. For each email row:
            - Extracts the `MessageId`, sender, subject, and date.
            - Sends a POST request to fetch the email content using the extracted `MessageId`.
            - Parses and processes the AJAX response to extract email data.
            - Creates or retrieves a user and prepares email data for saving.
        5. Saves the processed emails if any.

        Args:
            *args: Positional arguments (not used).
            **options: Keyword arguments (not used).

        Returns:
            None

        Logs:
            - Information, warnings, and errors are logged at various steps of the process.
        """

        bot_id = options.get('bot_id')

        logger = None
        if bot_id:
            logger = logging.getLogger(f'bot_{bot_id}_{self.command_name}')
        else:
            logger = logging.getLogger('pull_email')
        logger.info(f'Pull Email got bot id = {bot_id} ')

        # Retrieve session from another command
        logger.info(f'Fetching session via Login service for bot = {bot_id}...')

        session = SessionManager.get_session(bot_id=bot_id)
        if not session:
            logger.error(f"Failed to retrieve session for bot = {bot_id}.")
            return

        logger.info(f"Attempting to fetch inbox page for bot = {bot_id}: {settings.INBOX_URL}")
        try:
            response = session.get(settings.INBOX_URL)
            logger.info(f"Inbox page response status code for bot = {bot_id}: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"Failed to fetch the inbox page, status code for bot = {bot_id}: {response.status_code}")
                return

            parser = LexborHTMLParser(response.text)
            compressed_viewstate = parser.css_first(settings.COMPRESSED_VIEWSTATE_ID)

            if compressed_viewstate:
                compressed_viewstate_value = compressed_viewstate.attributes.get('value', '')
                logger.debug(f"COMPRESSEDVIEWSTATE found, length: {len(compressed_viewstate_value)}")
            else:
                logger.error("COMPRESSEDVIEWSTATE not found in the HTML.")
                return

            email_rows = parser.css(settings.EMAIL_ROWS_CSS_SELECTOR)
            logger.info(f"Found {len(email_rows)} email rows")

            if not email_rows:
                logger.info(f"No email rows found for bot = {bot_id}. Check the logs above for more information.")
                return

            emails_to_save = []

            for i, row in enumerate(email_rows):
                logger.debug(f"Processing email row {i+1} for bot = {bot_id}")
                if settings.TEST_MODE and i >= 3:
                    logger.info(f"Test mode: stopping after 3 emails for bot = {bot_id}")
                    break

                row_html = row.html
                message_id_match = re.search(r'(Command="REPLY"\s+MessageId="(\d+)"|messageid="(\d+)")', row_html, re.IGNORECASE)

                if message_id_match:
                    message_id = message_id_match.group(2) or message_id_match.group(3)
                    logger.debug(f"Found MessageId: {message_id}")
                else:
                    message_id = None
                    logger.error(f"MessageId not found in row {i+1}.")

                from_elem = row.css_first(settings.FROM_ELEMENT_CSS_SELECTOR)
                subject_elem = row.css_first(settings.SUBJECT_ELEMENT_CSS_SELECTOR)
                date_elem = row.css_first(settings.DATE_ELEMENT_CSS_SELECTOR)

                from_text = from_elem.text() if from_elem else 'Not found'
                subject_text = subject_elem.text() if subject_elem else 'Not found'
                date_text = date_elem.text() if date_elem else 'Not found'

                logger.info(f"Extracted email data: MessageId={message_id}, From={from_text}, Subject={subject_text}, Date={date_text}")

                if message_id:
                    post_data = {
                        '__EVENTTARGET': settings.PULL_EMAIL_EVENTTARGET,
                        '__EVENTARGUMENT': f'rc{i}',
                        '__COMPRESSEDVIEWSTATE': compressed_viewstate_value,
                        '__ASYNCPOST': settings.ASYNCPOST,
                        'ctl00$topScriptManager': settings.TOPSCRIPTMANAGER
                    }

                    form = MultipartEncoder(fields=post_data)
                    headers = HEADERS.copy()
                    headers['Content-Type'] = form.content_type

                    logger.info(f"Sending POST request for email {message_id} for bot = {bot_id}")
                    email_response = session.post(settings.INBOX_URL, data=form.to_string(), headers=headers)
                    logger.info(f"Email response status code: {email_response.status_code} for bot = {bot_id}")

                    if email_response.status_code == 200:
                        email_content = self.parse_ajax_response(email_response.text)
                        if email_content:
                            email_data = self.process_email_content(email_content, message_id, logger=logger)
                            if email_data:
                                user_id = get_or_create_user(email_data)
                                if user_id:
                                    email_to_save = {
                                        'user_id': user_id,
                                        'sent_datetime': email_data['date'],
                                        'subject': email_data['subject'],
                                        'body': email_data['message'],
                                        'message_id': email_data['message_id'],
                                        'bot_id' : bot_id
                                    }
                                    emails_to_save.append(email_to_save)
                                    logger.info(f"Processed email: {email_to_save} for bot = {bot_id}")
                                else:
                                    logger.warning(f"Failed to ensure user exists for email: {email_data['message_id']} bot = {bot_id}")
                            else:
                                logger.warning(f"Failed to process email content for message ID {message_id}. bot = {bot_id}")
                        else:
                            logger.error(f"Failed to parse AJAX response for message ID {message_id}. bot = {bot_id}")
                    else:
                        logger.error(f"Failed to fetch email content, status code: {email_response.status_code}. bot = {bot_id}")

                else:
                    logger.warning(f"Failed to extract message ID for email {i+1}. bot = {bot_id}")

                if settings.TEST_MODE and i >= 2:
                    logger.info("Test mode: stopping after 3 emails")
                    break

            if emails_to_save:
                save_emails(emails_to_save)

        except Exception as e:
            logger.error(f"An error occurred while processing emails for bot = {bot_id}: {str(e)}.", exc_info=True)

    def parse_ajax_response(self, response_text):
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

    def process_email_content(self, content, message_id, logger):
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
        most_recent_message = self.extract_most_recent_message(full_message)

        result = {
            'message_id': message_id,
            'from': from_text.attributes.get('value') if from_text else 'Not found',
            'date': date_text.attributes.get('value') if date_text else 'Not found',
            'subject': subject_text.attributes.get('value') if subject_text else 'Not found',
            'message': most_recent_message
        }

        logger.debug(f"Processed email content: {result}")
        return result

    def extract_most_recent_message(self, full_message):
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
