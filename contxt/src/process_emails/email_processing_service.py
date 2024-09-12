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
        """
        logger = logging.getLogger(f'bot_{self.bot_id}_{self.module_name}')
        emails = self._get_emails_for_processing()

        for email in emails:
            if 'text' in email.subject.lower():
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
        """
        return Email.objects.filter(is_processed=False, bot__id=self.bot_id)

    def _process_email(self, email_data, logger=None):
        """
        Processes an individual email to detect commands, extract phone numbers,
        and handle the appropriate actions (such as adding, updating, or removing contacts).

        Args:
            email_data (dict): A dictionary containing the following keys:
                - bot: The bot that processed the email.
                - user_id: The ID of the user who sent the email.
                - subject: The subject of the email which contains the command.
                - body: The body of the email.
                - message_id: The unique message ID of the email.
                - email_id: The unique email ID in the system.
            logger (logging.Logger, optional): A logger instance to log the email processing steps.

        Process:
            1. Detect Commands and Phone Numbers:
            - Extracts potential commands and phone numbers from the email subject.

            2. Command Execution:
            - Calls _process_command() to handle the appropriate command based on
                the detected command and phone numbers (e.g., add, update, remove).

            3. Email Status Update:
            - Marks the email as processed in the database by updating the is_processed field.

            4. Construct Response:
            - Calls _construct_response_message() to generate and send a response
                to the user based on the success or failure of the operation.

        Logging:
            Logs the status and details of email processing, including whether the
            operation succeeded and any errors or failures encountered.

        Example:
            email_data = {
                'bot': bot_instance,
                'user_id': 123,
                'subject': "Add Contact Email John john@example.com",
                'body': "Please add this contact.",
                'message_id': 'msg123',
                'email_id': 456
            }
            logger = logging.getLogger('email_processor')
            _process_email(email_data, logger)
        """
        commands, phone_numbers = self.detect_commands_and_phone_numbers(email_data['subject'])
        success, details, failed_contacts, new_contacts = self._process_command(email_data, commands, phone_numbers)
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

    def detect_commands_and_phone_numbers(self, input_string):
        """
        Detects commands and phone numbers from a given input string, typically the email subject.

        Args:
            input_string (str): The input string from which commands and phone numbers are to be detected,
                                usually the subject of the email.

        Process:
            1. Clean Input String:
            - Converts the input string to lowercase for case-insensitive command detection.

            2. Detect Commands:
            - Uses fuzzy matching (fuzzywuzzy library) to compare the input string with the list of valid commands.
            - If the similarity score exceeds the defined threshold (SIMILARITY_THRESHOLD),
                the command is considered detected and added to the `found_commands` set.

            3. Detect Phone Numbers:
            - Uses a regular expression (PHONE_REGEX) to extract phone numbers from the input string.
            - Each phone number is cleaned (i.e., removing extra characters) using the `clean_phone_number` method.

        Returns:
            tuple:
                - found_commands (set): A set of detected commands from the input string.
                - clean_phone_numbers (list): A list of cleaned phone numbers extracted from the input string.

        Example:
            input_string = "Add Contact Number John +1234567890"
            found_commands, phone_numbers = detect_commands_and_phone_numbers(input_string)
            # found_commands = {'Add Contact Number'}
            # phone_numbers = ['+1234567890']
        """
        input_string_cleaned = input_string.lower()
        found_commands = set()

        for command in self.COMMANDS:
            command_lower = command.lower()
            best_match, confidence = process.extractOne(input_string_cleaned, [command_lower])
            if confidence >= self.SIMILARITY_THRESHOLD:
                found_commands.add(command)

        phone_numbers = re.findall(self.PHONE_REGEX, input_string)
        clean_phone_numbers = [self.clean_phone_number(number) for number in phone_numbers]

        return found_commands, clean_phone_numbers

    def clean_phone_number(self, phone_number):
        cleaned = re.sub(r'[^\d+]', '', phone_number)
        if '+' in cleaned and not cleaned.startswith('+'):
            cleaned = cleaned.replace('+', '')
        return cleaned

    def _process_command(self, email_data, commands, phone_numbers):
        """
        Processes the detected commands from the email subject and executes the appropriate action
        (add, update, or remove a contact, or retrieve the contact list).

        Args:
            email_data (dict): A dictionary containing the following keys:
                - bot: The bot processing the email.
                - user_id: The ID of the user who sent the email.
                - subject: The subject of the email, which contains the command and contact details.
                - body: The body of the email.
                - message_id: The unique message ID for tracking purposes.
                - email_id: The unique email ID in the system.
            commands (set): A set of commands detected from the email subject (e.g., 'Add Contact Email', 'Update Contact Number').
            phone_numbers (list): A list of phone numbers extracted from the email subject.

        Process:
            1. Handle Email Commands:
            - If the command involves an email (e.g., 'Add Contact Email' or 'Update Contact Email'),
                it parses the contact name and email from the subject, validates the email,
                and performs the add/update operation.

            2. Handle Phone Number Commands:
            - If the command involves a phone number (e.g., 'Add Contact Number' or 'Update Contact Number'),
                it parses the contact name and phone number, validates the phone number,
                and performs the add/update operation.

            3. Handle Remove Command:
            - If the command is 'Remove Contact', it attempts to find and remove the specified contact.
            - If the contact is not found, it returns the 'CONTACT_NOT_FOUND' response.

            4. Handle Contact List Command:
            - If the command is 'Contact List', it retrieves the user's contact list and returns it.

            5. Return Response Details:
            - Based on the result of the operation (add, update, remove, or list), the method returns
                a tuple containing:
                - success (bool): Indicates whether the operation was successful.
                - details (str): A message key indicating the result (e.g., 'FAMILY_CONTACT_UPDATE', 'CONTACT_NOT_FOUND').
                - failed_contacts (list): A list of contacts that failed to process, along with error messages.
                - new_contacts (list): A list of newly added contacts (if applicable).

        Returns:
            tuple:
                - success (bool): Indicates whether the command was successfully processed.
                - details (str): The message key for the response message (e.g., 'FAMILY_CONTACT_UPDATE', 'CONTACT_NOT_FOUND').
                - failed_contacts (list): A list of failed contact processing attempts.
                - new_contacts (list): A list of new contacts created during the process (if applicable).

        Example:
            commands = {'Add Contact Email'}
            phone_numbers = []
            success, details, failed_contacts, new_contacts = _process_command(
                email_data={
                    'bot': bot_instance,
                    'user_id': 123,
                    'subject': "Add Contact Email John john@example.com",
                    'body': "Please add this contact.",
                    'message_id': 'msg123',
                    'email_id': 456
                },
                commands=commands,
                phone_numbers=phone_numbers
            )
        """
        failed_contacts = []
        new_contacts = []

        # Check if the command involves adding or updating an email
        if any("Email" in command for command in commands):
            name, email, _ = self._parse_contact_info(email_data)
            if not self._validate_email(email):
                failed_contacts.append(f"Invalid email address: {email_data.get('subject')}")
                return False, "FAMILY_CONTACT_UPDATE", failed_contacts, new_contacts

            # Handle adding contact by email
            if any("Add" in command for command in commands):
                success, contact_name = self._handle_contact(email_data, 'add', 'email', email, failed_contacts)
                if success and contact_name:
                    new_contacts.append(contact_name)
                return success, "FAMILY_CONTACT_UPDATE", failed_contacts, new_contacts

            # Handle updating contact by email
            if any("Update" in command for command in commands):
                name, email, _ = self._parse_contact_info(email_data)
                contact_found = self._find_contact(email_data['user_id'], name)
                if not contact_found:
                    return False, "CONTACT_NOT_FOUND", failed_contacts, new_contacts
                success, contact_name = self._handle_contact(email_data, 'update', 'email', email, failed_contacts)
                return success, "FAMILY_CONTACT_UPDATE", failed_contacts, new_contacts

        # Handle phone number-related commands
        if any("Number" in command for command in commands):
            if phone_numbers:
                if any("Add" in command for command in commands):
                    success, contact_name = self._handle_contact(email_data, 'add', 'phone_number', phone_numbers[0], failed_contacts)
                    if success and contact_name:
                        new_contacts.append(contact_name)
                    return success, "FAMILY_CONTACT_UPDATE", failed_contacts, new_contacts

                if any("Update" in command for command in commands):
                    name, email, _ = self._parse_contact_info(email_data)
                    contact_found = self._find_contact(email_data['user_id'], name)
                    if not contact_found:
                        return False, "CONTACT_NOT_FOUND", failed_contacts, new_contacts
                    success, contact_name = self._handle_contact(email_data, 'update', 'phone_number', phone_numbers[0], failed_contacts)
                    return success, "FAMILY_CONTACT_UPDATE", failed_contacts, new_contacts

        # Handle remove contact command
        if any("Remove" in command for command in commands):
            success, contact_name = self._remove_contact(email_data)
            if not success:
                return False, "CONTACT_NOT_FOUND", failed_contacts, new_contacts
            return success, "FAMILY_CONTACT_UPDATE", failed_contacts, new_contacts

        # Handle contact list command
        if any("Contact List" in command for command in commands):
            success = self._contact_list(email_data)
            return success, "CONTACT_LIST", failed_contacts, new_contacts

        return False, "INSTRUCTIONAL_ERROR", failed_contacts, new_contacts

    def _find_contact(self, user_id, contact_name):
        """
        Finds a contact for a given user based on the contact name.

        Args:
            user_id (int): The ID of the user.
            contact_name (str): The name of the contact to find.

        Returns:
            Contact: The contact object if found, None otherwise.
        """
        return Contact.objects.filter(user=user_id, contact_name=contact_name).first()

    def _handle_contact(self, email_data, action, detail_type, detail_value, failed_contacts):
        """
        Handles the addition or update of a contact based on the provided action.

        Args:
            email_data (dict): A dictionary containing the following keys:
                - bot: The bot processing the email.
                - user_id: The ID of the user requesting the contact modification.
                - subject: The subject of the email, containing the command and contact details.
                - body: The body of the email.
                - message_id: The unique message ID for tracking purposes.
                - email_id: The unique email ID in the system.
            action (str): The action to perform, either 'add' or 'update'.
            detail_type (str): Specifies whether the detail being handled is an 'email' or 'phone_number'.
            detail_value (str): The value of the email or phone number to be added or updated.
            failed_contacts (list): A list of failed contact processing attempts. If validation fails,
                                    an error message is appended to this list.

        Process:
            1. Parse Contact Info:
            - Extracts the contact name from the email subject using the _parse_contact_info() method.

            2. Validate Contact Details:
            - Calls _validate_contact_details() to check the validity of the contact name,
                email, or phone number. If invalid, the error is added to `failed_contacts`.

            3. Perform Add/Update Action:
            - If validation succeeds, either adds a new contact or updates an existing contact.
            - Uses Django's update_or_create() method to handle both 'add' and 'update' actions
                based on the `action` parameter.

        Returns:
            tuple:
                - success (bool): Indicates whether the operation succeeded or failed.
                - contact_name (str): The name of the contact being added or updated.

        Example:
            email_data = {
                'bot': bot_instance,
                'user_id': 123,
                'subject': "Add Contact Number John +1234567890",
                'body': "Please add this contact.",
                'message_id': 'msg123',
                'email_id': 456
            }
            failed_contacts = []
            success, contact_name = _handle_contact(email_data, 'add', 'phone_number', '+1234567890', failed_contacts)
        """
        name, _, _ = self._parse_contact_info(email_data)
        valid, message = self._validate_contact_details(name, **{detail_type: detail_value})

        # Add 'command' from email_data to message_args for failed contacts
        command_key = email_data.get('subject', '')  # Capture the original command for message_args

        if not valid:
            failed_contacts.append(f"{command_key}: {self._get_failed_contact_message(message)}")
            return False, name

        defaults = {detail_type: detail_value}
        contact, created = Contact.objects.update_or_create(
            user=email_data['user_id'], contact_name=name,
            defaults=defaults
        )

        if action == 'add' and created:
            return True, name
        return True, name

    def _remove_contact(self, email_data):
        name, _, _ = self._parse_contact_info(email_data)
        contact = Contact.objects.filter(user=email_data['user_id'], contact_name=name).first()
        if contact:
            contact.delete()
            return True, name
        return False, name

    def _contact_list(self, email_data):
        return True

    def _parse_contact_info(self, email_data):
        """
        Parses the contact information (name, email, phone number) from the email subject line.

        Args:
            email_data (dict): A dictionary containing the following keys:
                - bot: The bot processing the email.
                - user_id: The ID of the user who sent the email.
                - subject: The subject of the email, which contains the command and contact details.
                - body: The body of the email.
                - message_id: The unique message ID for tracking purposes.
                - email_id: The unique email ID in the system.

        Process:
            1. Extract Content from Subject:
            - Strips extra spaces and extracts the subject line from the email.

            2. Identify Email:
            - Attempts to match and extract the email address using a regular expression.
            - If no email is found, returns None for the email field.

            3. Identify Phone Number:
            - Uses a regular expression to detect a phone number in the subject.
            - If no phone number is found, returns None for the phone field.

            4. Extract Contact Name:
            - Removes the detected command, email, and phone number from the subject
                to isolate the contact name.
            - Strips any remaining spaces from the contact name.

        Returns:
            tuple:
                - name (str): The contact name extracted from the subject. If no name is found, returns None.
                - email (str or None): The email address extracted from the subject, or None if not found.
                - phone (str or None): The phone number extracted from the subject, or None if not found.

        Example:
            email_data = {
                'bot': bot_instance,
                'user_id': 123,
                'subject': "Add Contact Email John john@example.com",
                'body': "Please add this contact.",
                'message_id': 'msg123',
                'email_id': 456
            }
            name, email, phone = _parse_contact_info(email_data)
        """
        try:
            content = email_data['subject'].strip()

            # Split by spaces and assume the last part is the email
            parts = content.split()
            email = parts[-1] if re.match(self.EMAIL_REGEX, parts[-1]) else None

            # Handle phone number extraction
            phone_match = re.search(self.PHONE_REGEX, content)
            phone = phone_match.group(0) if phone_match else None

            # Remove command and email/phone from the content to extract the name
            command_removed = re.sub(r'|'.join([re.escape(command) for command in self.COMMANDS]), '', content, flags=re.IGNORECASE)
            command_removed = re.sub(self.EMAIL_REGEX, '', command_removed).strip()
            name = re.sub(self.PHONE_REGEX, '', command_removed).strip()

            return name, email, phone
        except Exception as e:
            logger = logging.getLogger(f'bot_{self.bot_id}_{self.module_name}')
            logger.error(f"Error parsing contact info: {e}")
            return None, None, None

    def _validate_contact_details(self, name, email=None, phone_number=None):
        """
        Validates the contact details, including the contact name, email, and phone number.

        Args:
            name (str): The name of the contact. This is required for all operations.
            email (str, optional): The email address to validate. Defaults to None if not provided.
            phone_number (str, optional): The phone number to validate. Defaults to None if not provided.

        Process:
            1. Validate Email:
            - If an email is provided, it is stripped of extra spaces and validated using the `_validate_email` method.
            - If the email is invalid, the method returns `False` with the error message "INVALID_EMAIL".

            2. Validate Phone Number:
            - If a phone number is provided, it is stripped of extra spaces and validated using the `_validate_phone_number` method.
            - If the phone number is invalid, the method returns `False` with the error message "INVALID_PHONE_NUMBER".

            3. Validate Contact Name:
            - Ensures that the contact name is provided. If the name is missing or empty, the method returns `False` with the error message "CONTACT_NAME_REQUIRED".

            4. Return Valid Status:
            - If all validations pass, the method returns `True` with an empty message, indicating that the contact details are valid.

        Returns:
            tuple:
                - valid (bool): Indicates whether the contact details are valid (True if valid, False if any validation fails).
                - message (str): An error message explaining why the validation failed (e.g., "INVALID_EMAIL", "INVALID_PHONE_NUMBER", or "CONTACT_NAME_REQUIRED").
                                Returns an empty string if validation succeeds.

        Example:
            # Validating a contact with both email and phone number
            valid, message = _validate_contact_details(name="John Doe", email="john@example.com", phone_number="+1234567890")
            # valid = True, message = ""

            # Validating a contact with an invalid email
            valid, message = _validate_contact_details(name="John Doe", email="invalid-email")
            # valid = False, message = "INVALID_EMAIL"
        """
        # Strip extra spaces before validating
        if email:
            email = email.strip()

        if email and not self._validate_email(email):
            return False, "INVALID_EMAIL"

        if phone_number:
            phone_number = phone_number.strip()

        if phone_number and not self._validate_phone_number(phone_number):
            return False, "INVALID_PHONE_NUMBER"

        if not name:
            return False, "CONTACT_NAME_REQUIRED"

        return True, ""

    def _validate_email(self, email):
        # Ensure no spaces and match the email format
        if not email or ' ' in email or not re.match(self.EMAIL_REGEX, email):
            return False
        return True

    def _validate_phone_number(self, phone):
        phone_match = re.match(self.PHONE_REGEX, phone)
        if phone_match:
            cleaned_phone = self.clean_phone_number(phone)
            logger = logging.getLogger(f'bot_{self.bot_id}_{self.module_name}')
            logger.debug(f"Validating phone number: Raw: {phone}, Cleaned: {cleaned_phone}")
            if len(cleaned_phone) >= 10:
                return True
        return False

    def _get_failed_contact_message(self, message_key):
        if message_key == "CONTACT_NAME_REQUIRED":
            return "Missing contact name."
        elif message_key == "INVALID_PHONE_NUMBER":
            return "Invalid phone number."
        elif message_key == "INVALID_EMAIL":
            return "Invalid email address."
        return "Unknown error."

    def _construct_response_message(self, user_id, success, message_key, message_args, message_id, email_id, bot, logger, new_contacts=[]):
        """
        Constructs and sends a response message to the user based on the outcome of the command processing.

        Args:
            user_id (int): The ID of the user who sent the email and is receiving the response.
            success (bool): Indicates whether the operation (add/update/remove contact) was successful.
            message_key (str): The key used to identify the type of response message template (e.g., 'FAMILY_CONTACT_UPDATE', 'CONTACT_NOT_FOUND').
            message_args (dict): A dictionary of dynamic values (e.g., contact details, failed contacts) to format into the response message template.
            message_id (str): The ID of the original message for tracking purposes.
            email_id (int): The unique ID of the email being processed.
            bot (BotAccount): The bot instance handling the communication.
            logger (logging.Logger): A logger instance to log the message construction and sending process.
            new_contacts (list): A list of new contacts created during the processing, if any.

        Process:
            1. Fetch Response Template:
            - Queries the database to retrieve the appropriate response message template based on the `message_key`.

            2. Add User Information:
            - Retrieves and includes the user's first name in the message (or defaults to 'User' if not available).

            3. Add Bot Accounts:
            - Fetches all bot accounts and includes their email addresses in the message to display available bots.

            4. Add Contact Information:
            - Dynamically populates the response message with the user's contact list and any newly added contacts.

            5. Handle Special Cases:
            - If the message is for certain keys like 'INSTRUCTIONAL_ERROR', it adds additional details such as previous SMS status.

            6. Send Message:
            - Formats the message with all dynamic content and sends it using the `push_emails` Django command to notify the user.

        Returns:
            None: This method does not return a value, but sends an email as the response.

        Example:
            message_args = {
                'command': 'Add Contact Email',
                'detail': ' (Add Contact Email John john@example.com)',
                'failed_contacts': 'No failed contacts'
            }
            _construct_response_message(
                user_id=123,
                success=True,
                message_key='FAMILY_CONTACT_UPDATE',
                message_args=message_args,
                message_id='msg123',
                email_id=456,
                bot=bot_instance,
                logger=logging.getLogger('email_processor'),
                new_contacts=['John']
            )
        """
        logger.info(f"User {user_id} | Success: {success} | Message Key: {message_key} | Message ID: {message_id}")
        try:
            # Fetch the corresponding message template from the database
            response_message = ResponseMessages.objects.filter(message_key=message_key).first()

            # Get the user's first name, defaulting to 'User' if it's not available
            first_name = user_id.name
            message_args['first_name'] = first_name

            # Get all bot accounts and prepare a string with their email addresses
            all_bot_accounts = BotAccount.objects.all()
            bot_accounts_str = '\n'.join([f"{bot.email_address}" for bot in all_bot_accounts])
            message_args['bot_accounts'] = bot_accounts_str

            # Fetch current contact list for the user
            all_contacts_for_user = Contact.objects.filter(user=user_id)
            contact_list_str = '\n'.join([f"{contact.contact_name}: {contact.email if contact.email else ''} : {contact.phone_number if contact.phone_number else ''}" for contact in all_contacts_for_user])

            # Add new contacts to message_args dynamically
            message_args['new_contacts'] = ', '.join(new_contacts) if new_contacts else 'No new contacts'

            if message_key == 'INSTRUCTIONAL_ERROR':
                # Add previous text message status
                contact = Contact.objects.filter(user=user_id).first()
                if contact:
                    # Fetch the last 20 SMS messages for the user's contact
                    last_20_sms = SMS.objects.filter(contact=contact).order_by('-created_at')[:20]
                    previous_text_messages_status = self._format_sms_status(last_20_sms)
                    message_args['previous_text_messages_status'] = previous_text_messages_status
                else:
                    message_args['previous_text_messages_status'] = 'No previous messages found.'

            if message_key in ['FAMILY_CONTACT_UPDATE', 'CONTACT_NOT_FOUND', 'CONTACT_LIST']:
                # Add the contact list for relevant message keys
                message_args['existing_contacts'] = contact_list_str
                message_args.setdefault('failed_contacts', 'No failed contacts')

            # Format the message with the provided arguments
            if response_message:
                formatted_message = response_message.response_content.format(**message_args)

                # Send the formatted message as an email using the call_command
                call_command('push_emails', message_id=message_id, message_content=formatted_message, bot_id=self.bot_id)

                logger.info(f"Response sent: {formatted_message}")

        except Exception as e:
            logger.error(f'Error constructing response message: {e}')

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
                f"MESSAGE ID: {sms.text_id or 'N/A'} | "
                f"DELIVERED: {sms.status}"
            )

        return '\n'.join(formatted_sms_list)
