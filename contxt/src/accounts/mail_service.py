
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta

import logging

logger = logging.getLogger('mail_box')

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
        logger.info("Logged in mailbox")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Logs out from the mailbox and closes the connection.

        This method is called when exiting the context of a 'with' statement.
        It ensures that the mailbox connection is properly closed.
        """
        self.mail.logout()
        logger.info("Logged out from mailbox")

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
            logger.info(f"Connected to: {self.email_url}")
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to {self.email_url}: {e}")
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
            logger.info(f"Logged in as {self.user_name}")
        except Exception as e:
            logger.error(f"Login failed for {self.user_name}: {e}")
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
            logger.info("Selected inbox")
        except Exception as e:
            logger.error(f"Failed to select inbox: {e}")
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
                logger.info(f"Found {len(messages[0].split())} messages matching criteria.")
                return messages[0].split()
            else:
                logger.warning("No messages found matching criteria.")
                return []
        except Exception as e:
            logger.error(f"Failed to search mail: {e}.")
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
            logger.info(f"Sorted email IDs: {sorted_ids}")
            return sorted_ids
        except ValueError as e:
            logger.error(f"Failed to sort email IDs: {e}")
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
            logger.info(f"Processing invite email ID: {email_id}")
            status, msg_data = self.mail.fetch(email_id, "(RFC822)")
            logger.info(f"Fetch status: {status}")
            if status == "OK":
                return msg_data
            else:
                logger.error(f"Failed to fetch email ID {email_id}: {status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching email ID {email_id}: {e}")
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
                    if "Person in Custody:" in subject or "Person in" in subject:
                        body = self.get_email_body(msg)
                        invite_code, full_name = self.extract_invite_code_and_name(subject, body)
                        if invite_code and full_name:
                            return invite_code, full_name
        except Exception as e:
            logger.error(f"Error processing email: {e}")
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
        logger.info(f"Email subject: {subject}, Date: {date}")
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
            logger.error(f"Failed to get email body: {e}")
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
                logger.info(f"Found invite code: {invite_code}")

                # Extract full name from subject
                name_part = subject.split(":")[1].strip()
                last_name, first_name = name_part.split(", ")
                full_name = f"{first_name} {last_name}"
                logger.info(f"Extracted full name: {full_name}")

                return invite_code, full_name
            else:
                logger.warning("Invite code not found in the email body")
                return None, None
        except Exception as e:
            logger.error(f"Error extracting invite code and name: {e}")
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
            logger.info(f"Successfully deleted invite email with ID: {email_id}")
        except Exception as e:
            logger.error(f"Failed to delete invite email: {str(e)}")
            raise
