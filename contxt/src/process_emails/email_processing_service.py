from core.models import Contact, ContactManagementResponseMessages
from process_emails.models import Email
from contxt.utils.constants import CURRENT_TASKS_RUN_BY_BOTS

from django.core.management import call_command

from fuzzywuzzy import process
import re
import logging

class EmailProcessingHandler:
    """
    The EmailProcessingHandler class is responsible for processing emails that contain
    contact management commands (such as adding, updating, or removing contacts),
    detecting commands and phone numbers, and responding to the users.

    Attributes:
        bot_id (int): The identifier for the bot processing the emails.
        module_name (str): The name of the module (e.g., 'contact_management').
    """

    COMMANDS = [
        "Add Contact Email",
        "Add Contact Number",
        "Update Contact Email",
        "Update Contact Number",
        "Remove Contact",
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
        Retrieves all unprocessed emails for the bot and processes each one.

        It loops through emails and passes them to the _process_email method to detect
        commands and act accordingly (e.g., add, update, remove contacts).
        """
        logger = logging.getLogger(f'bot_{self.bot_id}_{self.module_name}')
        emails = self._get_emails_for_processing()

        for email in emails:
            if 'text' in email.subject.lower():
                # TODO improve this logic
                logger.info(f"Skipping email with subject '{email.subject}' because it contains 'text' which is part of a valid command.")
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
        Fetches all unprocessed emails associated with the bot.

        Returns:
            QuerySet: A Django QuerySet containing all unprocessed emails for this bot.
        """
        return Email.objects.filter(is_processed=False, bot__id=self.bot_id)

    def _process_email(self, email_data, logger=None):
        """
        Processes a single email by extracting commands and phone numbers from the subject,
        executing the relevant command, and constructing a response message.

        Args:
            email_data (dict): A dictionary containing email-related information such as:
                            bot, user_id, subject, body, message_id, and email_id.
            logger (logging.Logger, optional): Logger instance for logging the process flow.
        """

        # Detect commands and phone numbers in the email's subject line
        commands, phone_numbers = self.detect_commands_and_phone_numbers(email_data['subject'])

        # Process the detected command and handle contact addition, update, removal, or listing
        success, details = self._process_command(email_data, commands, phone_numbers)

        # Log the details of the processing outcome
        logger.info(f"Details = : {details}")

        # Mark the email as processed once the command is handled
        email_obj = Email.objects.filter(id=email_data['email_id']).first()
        if email_obj:
            email_obj.is_processed = True  # Mark the email as processed
            email_obj.save()  # Save the updated email status in the database

        # Construct and send the response message based on the outcome of the command
        self._construct_response_message(
            user_id=email_data['user_id'],  # User ID to whom the response is sent
            success=success,  # Whether the operation was successful
            message_key=details,  # The message key corresponding to the outcome
            message_args={'command': email_data.get('subject', ''),  # Command from the email subject
                        'detail': ' (' + email_data.get('subject') + ')'},  # Additional details
            message_id=email_data['message_id'],  # The ID of the original message
            email_id=email_data['email_id'],  # The ID of the email object
            bot=email_data['bot'],  # Bot instance that processed the email
            logger=logger  # Logger for tracking the response process
        )

    def detect_commands_and_phone_numbers(self, input_string):
        """
        Detects commands and phone numbers in a given input string (typically the email subject).

        Uses fuzzy matching for command detection and regular expressions for phone number extraction.

        Args:
            input_string (str): The input text from which commands and phone numbers are extracted.

        Returns:
            tuple: A set of detected commands and a list of cleaned phone numbers.
        """
        input_string_cleaned = input_string.lower()
        found_commands = set()

        # Use fuzzy matching to detect commands in the input string
        for command in self.COMMANDS:
            command_lower = command.lower()
            best_match, confidence = process.extractOne(input_string_cleaned, [command_lower])
            if confidence >= self.SIMILARITY_THRESHOLD:
                found_commands.add(command)

        # Extract phone numbers from the input string
        phone_numbers = re.findall(self.PHONE_REGEX, input_string)
        # Clean phone numbers and validate them
        clean_phone_numbers = [self.clean_phone_number(number) for number in phone_numbers]

        return found_commands, clean_phone_numbers

    def clean_phone_number(self, phone_number):
        """
        Cleans and formats a phone number by removing unwanted characters.

        Args:
            phone_number (str): The phone number to clean.

        Returns:
            str: The cleaned phone number, only containing digits.
        """
        cleaned = re.sub(r'[^\d+]', '', phone_number)
        if '+' in cleaned and not cleaned.startswith('+'):
            cleaned = cleaned.replace('+', '')
        return cleaned

    def _process_command(self, email_data, commands, phone_numbers):
        """
        Processes the detected commands and phone numbers extracted from the email subject.

        Based on the detected commands (Add, Update, Remove, Contact List), the appropriate handler
        is called to either add, update, remove a contact, or retrieve the contact list.

        Args:
            email_data (dict): Contains details of the email being processed (user ID, subject, etc.).
            commands (set): A set of commands detected from the email subject.
            phone_numbers (list): A list of extracted phone numbers from the email subject.

        Returns:
            tuple: A tuple containing:
                - success (bool): Indicates whether the operation was successful.
                - message (str): A message key indicating the result of the operation.
        """

        # Check if the command is "Add" and handle accordingly
        if any("Add" in command for command in commands):
            # If a phone number is detected, add it
            if phone_numbers:
                return self._handle_contact(email_data, 'add', 'phone_number', phone_numbers[0])
            # If no phone number, handle adding an email instead
            return self._handle_contact(email_data, 'add', 'email', self._parse_contact_info(email_data)[1])

        # Check if the command is "Update" and handle accordingly
        if any("Update" in command for command in commands):
            # If a phone number is detected, update it
            if phone_numbers:
                return self._handle_contact(email_data, 'update', 'phone_number', phone_numbers[0])
            # If no phone number, handle updating the email
            return self._handle_contact(email_data, 'update', 'email', self._parse_contact_info(email_data)[1])

        # Check if the command is "Remove" and handle removing a contact
        if any("Remove" in command for command in commands):
            return self._remove_contact(email_data)

        # Check if the command is "Contact List" and handle retrieving the contact list
        if any("Contact List" in command for command in commands):
            return self._contact_list(email_data)

        # If no recognized command was found, return an unknown command message
        return False, "UNKNOWN_COMMAND"

    def _handle_contact(self, email_data, action, detail_type, detail_value):
        """
        Handle adding or updating a contact based on the action.

        Args:
            email_data (dict): Data of the email being processed.
            action (str): The action to be performed ('add' or 'update').
            detail_type (str): Type of detail being handled ('email' or 'phone').
            detail_value (str): The value of the detail to be added or updated.

        Returns:
            tuple: A tuple where the first element is a boolean indicating success,
                   and the second element is a message string.
        """
        name, _, _ = self._parse_contact_info(email_data)
        valid, message = self._validate_contact_details(name, **{detail_type: detail_value})

        if valid:
            defaults = {detail_type: detail_value}
            contact, created = Contact.objects.update_or_create(
                user=email_data['user_id'], contact_name=name,
                defaults=defaults
            )
            if action == 'add':
                return True, "CONTACT_ADDED_SUCCESSFULLY" if created else "CONTACT_ALREADY_EXISTS"
            return True, "CONTACT_UPDATED_SUCCESSFULLY" if not created else "CONTACT_NOT_FOUND"

        return False, message

    def _remove_contact(self, email_data):
        """
        Removes a contact based on the email data.

        Args:
            email_data (dict): Data of the email being processed.

        Returns:
            tuple: A tuple where the first element is a boolean indicating success,
                   and the second element is a message string.
        """
        name, _, _ = self._parse_contact_info(email_data)
        contact = Contact.objects.filter(user=email_data['user_id'], contact_name=name).first()
        if contact:
            contact.delete()
            return True, "CONTACT_REMOVED_SUCCESSFULLY"
        return False, "CONTACT_NOT_FOUND"

    def _contact_list(self, email_data):
        """
        Retrieves the contact list for a user.

        Args:
            email_data (dict): Data of the email being processed.

        Returns:
            tuple: A tuple where the first element is a boolean indicating success,
                   and the second element is a string containing the contact list.
        """

        return True, 'CONTACT_LIST'

    def _parse_contact_info(self, email_data):
        """
        Parses contact information from the email subject.

        Args:
            email_data (dict): Data of the email being processed.

        Returns:
            tuple: A tuple containing the contact name, email, and phone number.
        """
        try:
            content = email_data['subject']
            email_match = re.search(self.EMAIL_REGEX, content)
            email = email_match.group(0) if email_match else None

            phone_match = re.search(self.PHONE_REGEX, content)
            phone = phone_match.group(0) if phone_match else None

            content_without_details = re.sub(r'|'.join([re.escape(command) for command in self.COMMANDS]), '', content, flags=re.IGNORECASE)
            content_without_details = re.sub(self.EMAIL_REGEX, '', content_without_details)
            content_without_details = re.sub(self.PHONE_REGEX, '', content_without_details)
            name = content_without_details.strip()

            return name, email, phone
        except Exception as e:
            logger = logging.getLogger(f'bot_{self.bot_id}_{self.module_name}')
            logger.error(f"Error parsing contact info: {e}")
            return None, None, None

    def _validate_contact_details(self, name, email=None, phone_number=None):
        """
        Validates the contact details provided.

        Args:
            name (str): The name of the contact.
            email (str, optional): The email of the contact.
            phone_number (str, optional): The phone number of the contact.

        Returns:
            tuple: A tuple where the first element is a boolean indicating validity,
                   and the second element is a message string.
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
        Validates an email address.

        Args:
            email (str): The email address to validate.

        Returns:
            bool: True if the email address is valid, False otherwise.
        """
        return re.match(self.EMAIL_REGEX, email) is not None

    def _validate_phone_number(self, phone):
        """
        Validates a phone number.

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

    def _construct_response_message(self, user_id, success, message_key, message_args, message_id, email_id, bot, logger):
        """
        Constructs and sends a response message to the user.

        Args:
            user_id (int): The ID of the user.
            success (bool): Indicates if the operation was successful.
            message_key (str): The key for the response message.
            message_args (dict): Arguments to format the response message.
            message_id (str): The ID of the email message.
            email_id (int): The ID of the email.
            bot (str): The bot identifier.
            logger (logging.Logger): The logger instance.
        """
        logger.info(f"User {user_id} | Success: {success} | Message Key: {message_key} | Message ID: {message_id}")
        try:
            response_message = ContactManagementResponseMessages.objects.filter(message_key=message_key).first()

            if response_message:
                if not message_key == 'CONTACT_LIST':
                    formatted_message = response_message.response_content.format(**message_args)
                all_contacts_for_user = Contact.objects.filter(user=user_id)

                # Format the contact list into a string
                contact_list_str = '\n'.join([f"{contact.contact_name}: {contact.email if contact.email else contact.phone_number}" for contact in all_contacts_for_user])

                # Fetch and format the contact list message
                contact_list_message = ContactManagementResponseMessages.objects.filter(message_key='CONTACT_LIST').first()
                if contact_list_message:
                    contact_list_message_content = contact_list_message.response_content.format(all_contacts=contact_list_str)
                    if not message_key == 'CONTACT_LIST':
                        formatted_message += "\n\n" + contact_list_message_content
                    else:
                        formatted_message = contact_list_message_content

                call_command('push_emails', message_id=message_id, message_content=formatted_message)

                logger.info(f"Response = {formatted_message}.")
        except Exception as e:
            logger.error(f'Error constructing response message: {e}')
