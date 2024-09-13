from core.models import Contact, ResponseMessages
from process_emails.models import Email
from accounts.models import BotAccount
from sms_app.models import SMS
from contxt.utils.constants import CURRENT_TASKS_RUN_BY_BOTS

from django.core.management import call_command

from fuzzywuzzy import process
import re
import logging


class EmailProcessingHandler:
    """
    The EmailProcessingHandler class is responsible for processing emails that contain
    contact management commands such as adding, updating, removing contacts, or retrieving
    the contact list. The class detects commands, extracts contact information such as phone
    numbers or email addresses, and responds accordingly.

    Attributes:
        bot_id (int): The identifier for the bot processing the emails.
        module_name (str): The name of the module (e.g., 'contact_management').
    """

    COMMANDS = [
        "Add",
        "Update",
        "Remove",
        "Contact List"
    ]
    EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    PHONE_REGEX = r'(?:\+?\d{1,4}[-.\s]?)?(?:\(?\d{1,5}\)?[-.\s]?)?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
    SIMILARITY_THRESHOLD = 90

    def __init__(self, bot_id):
        """
        Initializes the EmailProcessingHandler instance with a given bot ID.

        Args:
            bot_id (int): The ID of the bot that will process the emails.
        """
        self.bot_id = bot_id
        self.module_name = CURRENT_TASKS_RUN_BY_BOTS['contact_management']
        self.process_emails()

    def process_emails(self):
        """
        Retrieves all unprocessed emails associated with the bot and processes each one.
        It skips emails that contain only phone numbers or the word 'text' in the subject.

        The method fetches email data, detects commands and relevant information from the email
        subject, and processes the commands to add, update, or remove contacts.
        """
        logger = logging.getLogger(f'bot_{self.bot_id}_{self.module_name}')
        emails = self._get_emails_for_processing()

        for email in emails:
            if 'text' in email.subject.lower():
                logger.info(f"Skipping email with subject '{email.subject}' because it contains 'text' which is part of a valid command. This will be used in send_sms command.")
                continue

            # Skip emails where the subject is just a phone number
            if re.fullmatch(self.PHONE_REGEX, email.subject.strip()):
                logger.info(f"Skipping email with subject '{email.subject}' because it is just a phone number. This will be used in send_sms command.")
                continue

            email_data = {
                'bot': email.bot,
                'user_id': email.user,
                'subject': email.subject,
                'body': email.body,
                'message_id': email.message_id,
                'email_id': email.id
            }
            self._process_email(email_data, logger=logger)

    def _get_emails_for_processing(self):
        """
        Fetches all unprocessed emails for the bot.

        Returns:
            QuerySet: A queryset containing all emails that are not yet processed and are
            associated with the bot.
        """
        return Email.objects.filter(is_processed=False, bot__id=self.bot_id)

    def _process_email(self, email_data, logger=None):
        """
        Processes an individual email by detecting commands, extracting phone numbers or
        email addresses, and handling the appropriate actions (such as adding, updating,
        or removing contacts).

        Args:
            email_data (dict): Contains the email's data, including the subject, body, message_id,
            and email_id.
            logger (logging.Logger, optional): A logger instance to log processing details. Default is None.
        """
        command, contact_name, contact_detail, detail_type = self.detect_commands_and_contact_details(email_data['subject'])

        # Parse contact info based on the detected command
        contact_name, contact_detail, _ = self._parse_contact_info(email_data['subject'], command)

        success, details, failed_contacts, new_contacts = self._process_command(
            email_data, command, contact_name, contact_detail, detail_type
        )
        logger.info(f"Details = : {details}")

        email_obj = Email.objects.filter(id=email_data['email_id']).first()
        if email_obj:
            email_obj.is_processed = True
            email_obj.save()

        self._construct_response_message(
            user_id=email_data['user_id'],
            success=success,
            message_key=details,
            message_args={'command': email_data.get('subject', ''),
                          'detail': ' (' + email_data.get('subject') + ')',
                          'failed_contacts': '\n'.join(failed_contacts)},
            message_id=email_data['message_id'],
            email_id=email_data['email_id'],
            bot=email_data['bot'],
            logger=logger,
            new_contacts=new_contacts
        )

    def detect_commands_and_contact_details(self, input_string):
        """
        Detects commands and extracts contact names and contact details (phone numbers or email addresses)
        from the input string (email subject).

        Args:
            input_string (str): The subject of the email from which the command, contact name,
            and contact detail are to be detected.

        Returns:
            tuple:
                - found_command (str): The detected command ('Add', 'Update', 'Remove', or 'Contact List').
                - contact_name (str): The name of the contact (if applicable).
                - contact_detail (str): The email or phone number (if applicable).
                - detail_type (str): Either 'email' or 'phone_number' (if applicable).
        """
        input_string_cleaned = input_string.strip()

        # Extract the first word(s) for detecting command (first or second depending on command type)
        parts = input_string_cleaned.split()
        if len(parts) < 2:
            return None, None, None, None

        # Match command with fuzzy matching
        command_candidates = [' '.join(parts[:2]), parts[0]]  # Either first two words or first word
        found_command = None
        for candidate in command_candidates:
            best_match, confidence = process.extractOne(candidate, self.COMMANDS)
            if confidence >= self.SIMILARITY_THRESHOLD:
                found_command = best_match
                break

        if not found_command:
            return None, None, None, None

        # Handle Contact List separately
        if found_command == "Contact List":
            return found_command, None, None, None

        # Handle Remove separately: it doesn't contain contact details, only the name
        if found_command == "Remove":
            contact_name = ' '.join(parts[1:])
            return found_command, contact_name, None, None

        # Find contact detail (last element of string)
        contact_detail = parts[-1]
        contact_name = None

        # Determine if contact detail is phone number or email
        if re.match(self.EMAIL_REGEX, contact_detail):
            detail_type = 'email'
        elif re.match(self.PHONE_REGEX, contact_detail):
            detail_type = 'phone_number'
        else:
            detail_type = 'email'

        # Extract contact name based on command type
        if found_command in ["Add", "Update"]:  # One-word commands that need contact detail
            contact_name = ' '.join(parts[1:-1])

        return found_command, contact_name, contact_detail, detail_type

    def _process_command(self, email_data, command, contact_name, contact_detail, detail_type):
        """
        Processes the detected command and performs the appropriate action
        (e.g., adding, updating, or removing a contact).

        Args:
            email_data (dict): Contains the email's data, including the subject, body, and user_id.
            command (str): The detected command ('Add', 'Update', 'Remove', or 'Contact List').
            contact_name (str): The name of the contact to be added/updated/removed.
            contact_detail (str): The contact detail (email or phone number).
            detail_type (str): The type of the contact detail ('email' or 'phone_number').

        Returns:
            tuple:
                - success (bool): Indicates whether the operation was successful.
                - message_key (str): A key representing the result of the operation, used for constructing responses.
                - failed_contacts (list): A list of contacts that failed during processing.
                - new_contacts (list): A list of newly added contacts (if applicable).
        """
        failed_contacts = []
        new_contacts = []

        if command == "Add":
            success, contact_name = self._handle_contact(email_data, 'Add', detail_type, contact_detail, failed_contacts)
            if success and contact_name:
                new_contacts.append(contact_name)
            return success, "FAMILY_CONTACT_UPDATE", failed_contacts, new_contacts

        if command == "Update":
            contact_found = self._find_contact(email_data['user_id'], contact_name)
            if not contact_found:
                return False, "CONTACT_NOT_FOUND", failed_contacts, new_contacts
            success, contact_name = self._handle_contact(email_data, 'Update', detail_type, contact_detail, failed_contacts)
            return success, "FAMILY_CONTACT_UPDATE", failed_contacts, new_contacts

        if command == "Remove":
            contact_found = self._find_contact(email_data['user_id'], contact_name)
            if not contact_found:
                return False, "CONTACT_NOT_FOUND", failed_contacts, new_contacts
            contact_found.delete()
            return True, "FAMILY_CONTACT_UPDATE", failed_contacts, new_contacts

        if command == "Contact List":
            success = self._contact_list(email_data)
            return success, "CONTACT_LIST", failed_contacts, new_contacts

        return False, "INSTRUCTIONAL_ERROR", failed_contacts, new_contacts

    def _find_contact(self, user_id, contact_name):
        """
        Finds an existing contact for a given user based on the contact name.

        Args:
            user_id (int): The ID of the user.
            contact_name (str): The name of the contact to be found.

        Returns:
            Contact: The found contact object if it exists, or None if not found.
        """
        return Contact.objects.filter(user=user_id, contact_name=contact_name).first()

    def _handle_contact(self, email_data, action, detail_type, detail_value, failed_contacts):
        """
        Handles the addition or update of a contact based on the provided action.

        Args:
            email_data (dict): Contains the email's data, including the subject, body, and user_id.
            action (str): The action to perform, either 'Add' or 'Update'.
            detail_type (str): Specifies whether the detail being handled is 'email' or 'phone_number'.
            detail_value (str): The value of the email or phone number to be added or updated.
            failed_contacts (list): A list to store failed contact operations.

        Returns:
            tuple:
                - success (bool): Indicates whether the operation was successful.
                - contact_name (str): The name of the contact that was added or updated.
        """
        contact_name, contact_detail, _ = self._parse_contact_info(email_data['subject'], action)
        valid, message = self._validate_contact_details(contact_name, **{detail_type: contact_detail})

        if not valid:
            failed_contacts.append(f"Invalid {detail_type}: {contact_detail}")
            return False, contact_name

        defaults = {detail_type: detail_value}
        contact, created = Contact.objects.update_or_create(
            user=email_data['user_id'], contact_name=contact_name,
            defaults=defaults
        )

        return True, contact_name

    def _remove_contact(self, email_data):
        """
        Removes a contact for a given user based on the contact name.

        Args:
            email_data (dict): Contains the email's data, including the subject and user_id.

        Returns:
            tuple:
                - success (bool): Indicates whether the contact was successfully removed.
                - contact_name (str): The name of the removed contact.
        """
        contact_name, _, _ = self._parse_contact_info(email_data['subject'], "Remove")
        contact = Contact.objects.filter(user=email_data['user_id'], contact_name=contact_name).first()
        if contact:
            contact.delete()
            return True, contact_name
        return False, contact_name

    def _contact_list(self, email_data):
        """
        Retrieves the contact list for a user.

        Args:
            email_data (dict): Contains the email's data, including the user_id.

        Returns:
            bool: True if the user has contacts, False if no contacts are found.
        """
        contacts = Contact.objects.filter(user=email_data['user_id'])
        if contacts.exists():
            return True
        return False

    def _parse_contact_info(self, subject_string, command):
        """
        Parses the contact information (name and detail) from the email subject line based
        on the detected command.

        Args:
            subject_string (str): The subject of the email containing the command, contact name, and detail.
            command (str): The detected command from the subject line.

        Returns:
            tuple:
                - contact_name (str): The extracted contact name.
                - contact_detail (str): The email or phone number (if applicable).
                - None (None): A placeholder for a future parameter.
        """
        subject_cleaned = subject_string.strip()
        parts = subject_cleaned.split()

        # Handle the "Remove" command (no contact detail)
        if command == "Remove":
            contact_name = ' '.join(parts[1:])  # Everything after the command is the name
            return contact_name, None, None

        # Handle "Add" and "Update" commands
        if command in ["Add", "Update"]:
            if len(parts) < 3:  # Ensure there are enough parts to extract a name and a detail
                return None, None, None
            contact_detail = parts[-1]  # The last part is the contact detail (email/phone)
            contact_name = ' '.join(parts[1:-1])  # Everything between the command and the contact detail is the name
            return contact_name, contact_detail, None

        return None, None, None

    def _validate_contact_details(self, name, email=None, phone_number=None):
        """
        Validates the contact details, ensuring the contact name is present and that the
        email or phone number (if provided) is valid.

        Args:
            name (str): The contact name, which is required.
            email (str, optional): The email address to validate (if applicable).
            phone_number (str, optional): The phone number to validate (if applicable).

        Returns:
            tuple:
                - valid (bool): Indicates whether the contact details are valid.
                - message (str): The error message if validation fails, otherwise an empty string.
        """
        if email and not self._validate_email(email):
            return False, "INVALID_EMAIL"

        if phone_number and not self._validate_phone_number(phone_number):
            return False, "INVALID_PHONE_NUMBER"

        if not name:
            return False, "CONTACT_NAME_REQUIRED"

        return True, ""

    def _validate_email(self, email):
        """
        Validates the email format using a regular expression.

        Args:
            email (str): The email address to validate.

        Returns:
            bool: True if the email is valid, False otherwise.
        """
        if not email or ' ' in email or not re.match(self.EMAIL_REGEX, email):
            return False
        return True

    def _validate_phone_number(self, phone):
        """
        Validates the phone number format using a regular expression and ensures
        the cleaned phone number has at least 10 digits.

        Args:
            phone (str): The phone number to validate.

        Returns:
            bool: True if the phone number is valid, False otherwise.
        """
        phone_match = re.match(self.PHONE_REGEX, phone)
        if phone_match:
            cleaned_phone = self.clean_phone_number(phone)
            logger = logging.getLogger(f'bot_{self.bot_id}_{self.module_name}')
            logger.debug(f"Validating phone number: Raw: {phone}, Cleaned: {cleaned_phone}")
            if len(cleaned_phone) >= 10:
                return True
        return False

    def _construct_response_message(self, user_id, success, message_key, message_args, message_id, email_id, bot, logger, new_contacts=[]):
        """
        Constructs and sends a response message to the user based on the outcome of
        the email command processing (e.g., whether the contact was added, updated, or removed).

        Args:
            user_id (int): The ID of the user to whom the response will be sent.
            success (bool): Whether the operation succeeded.
            message_key (str): The key representing the type of response message.
            message_args (dict): Arguments to format into the response message.
            message_id (str): The ID of the original email message.
            email_id (int): The unique email ID in the system.
            bot (BotAccount): The bot instance processing the request.
            logger (logging.Logger): The logger instance for logging the response.
            new_contacts (list): A list of newly added contacts, if any.
        """
        logger.info(f"User {user_id} | Success: {success} | Message Key: {message_key} | Message ID: {message_id}")
        try:
            response_message = ResponseMessages.objects.filter(message_key=message_key).first()
            first_name = user_id.name
            message_args['first_name'] = first_name

            all_bot_accounts = BotAccount.objects.all()
            bot_accounts_str = '\n'.join([f"{bot.email_address}" for bot in all_bot_accounts])
            message_args['bot_accounts'] = bot_accounts_str

            all_contacts_for_user = Contact.objects.filter(user=user_id)
            contact_list_str = '\n'.join([f"{contact.contact_name}: {contact.email if contact.email else ''} : {contact.phone_number if contact.phone_number else ''}" for contact in all_contacts_for_user])
            message_args['new_contacts'] = ', '.join(new_contacts) if new_contacts else 'No new contacts'
            message_args['existing_contacts'] = contact_list_str

            recent_sms_sent_by_user = SMS.objects.filter(contact__user=user_id).order_by('-created_at')[:20]
            previous_text_messages_status = self._format_sms_status(recent_sms_sent_by_user)
            message_args['previous_text_messages_status'] = previous_text_messages_status


            if response_message:
                formatted_message = response_message.response_content.format(**message_args)
                call_command('push_emails', message_id=message_id, message_content=formatted_message, bot_id=self.bot_id)
                logger.info(f"Response sent: {formatted_message}")

        except Exception as e:
            logger.error(f'Error constructing response message: {e}')

    def clean_phone_number(self, phone_number):
        """
        Cleans a phone number by removing non-digit characters and ensures proper formatting.

        Args:
            phone_number (str): The raw phone number string.

        Returns:
            str: The cleaned phone number with non-numeric characters removed.
        """
        cleaned = re.sub(r'[^\d+]', '', phone_number)
        if '+' in cleaned and not cleaned.startswith('+'):
            cleaned = cleaned.replace('+', '')
        return cleaned

    def _format_sms_status(self, sms_queryset):
        """
        Formats the last 20 SMS messages into a readable string for the previous_text_messages_status.
        Args:
            sms_queryset (QuerySet): The last 20 SMS messages.
        Returns:
            str: A formatted string containing SMS details.
        """
        formatted_sms_list = []
        for sms in sms_queryset:
            formatted_sms_list.append(
                f"DATE: {sms.created_at.strftime('%Y-%m-%d')} | "
                f"TIME: {sms.created_at.strftime('%H:%M:%S')} | "
                f"CONTACT: {sms.contact.contact_name} | "
                f"STATUS: {sms.status}"
            )

        return '\n'.join(formatted_sms_list)
