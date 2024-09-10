from core.models import Contact, ContactManagementResponseMessages
from process_emails.models import Email
from contxt.utils.constants import CURRENT_TASKS_RUN_BY_BOTS

from django.core.management import call_command

from fuzzywuzzy import process

import re
import logging

logger = logging.getLogger(__name__)

# Helper function for detecting commands and phone numbers
def detect_commands_and_phone_numbers(input_string):
    # List of predefined commands
    commands = ["Add Contact Email", "Add Contact Number", "Update Contact Email", "Update Contact Number", "Remove Contact", "Contact List"]

    # Set a threshold for fuzzy matching (e.g., 90% similarity)
    similarity_threshold = 90

    # Tokenize input string into words (simple splitting on spaces)
    input_words = input_string.split()

    # Detect commands using fuzzy matching
    found_commands = []
    for word in input_words:
        # Find the closest matching command for each word in the input
        best_match, confidence = process.extractOne(word, commands)
        if confidence >= similarity_threshold:
            found_commands.append(best_match)

    # Regex pattern for US phone numbers
    phone_number_pattern = r'(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}'

    # Find all phone numbers in the string
    phone_numbers = re.findall(phone_number_pattern, input_string)

    # Clean the phone numbers
    clean_phone_numbers = [clean_phone_number(number) for number in phone_numbers]

    found_commands = set(found_commands)

    return found_commands, clean_phone_numbers

def clean_phone_number(phone_number):
    # Keep the leading + if it exists, and remove all non-numeric characters except +
    cleaned = re.sub(r'[^\d+]', '', phone_number)
    # Remove the + if it's not at the start of the phone number
    if '+' in cleaned and not cleaned.startswith('+'):
        cleaned = cleaned.replace('+', '')
    return cleaned

class EmailProcessingHandler:
    def __init__(self, bot_id):
        self.bot_id = bot_id
        self.module_name = 'contact_management'


        self.process_emails()

    def process_emails(self):
        """
        Fetch and process emails saved in the database.
        """
        logger = logging.getLogger(f'bot_{self.bot_id}_{self.module_name}')
        emails = self._get_emails_for_processing()

        for email in emails:
            email_data = {
                'bot': email.bot,
                'user_id': email.user,
                'subject': email.subject,
                'body': email.body,
                'message_id': email.message_id,
                'email_id' : email.id
            }
            self._process_email(email_data, logger=logger)

    def _get_emails_for_processing(self):
        """
        Retrieve emails that need to be processed from the database.
        """
        return Email.objects.filter(is_processed=False, bot__id=self.bot_id)

    def _process_email(self, email_data, logger=None):
        """
        Process a single email to determine and execute the required action.
        """
        commands, phone_numbers = detect_commands_and_phone_numbers(email_data['subject'])

        if any("Add" in command for command in commands):
            if phone_numbers:
                success, details = self._add_contact_number(email_data, phone_numbers[0])
            else:
                success, details = self._add_contact_email(email_data)

            try:
                logger.info(f'Success = {success}. Details = {details}')
            except Exception as e:
                logger.error(f'Error in adding contact phone or email = {e}')
        elif any("Update" in command for command in commands):
            if phone_numbers:
                success, details = self._update_contact_number(email_data, phone_numbers[0])
            else:
                success, details = self._update_contact_email(email_data)

            try:
                logger.info(f'Success = {success}. Details = {details}')
            except Exception as e:
                logger.error(f'Error in adding contact phone or email = {e}')
        elif any("Remove" in command for command in commands):
            success, details = self._remove_contact(email_data)

            try:
                logger.info(f'Success = {success}. Details = {details}')
            except Exception as e:
                logger.error(f'Error in adding contact phone or email = {e}')
        elif any("Contact List" in command for command in commands):
            success, details = self._contact_list(email_data)

            try:
                logger.info(f'Success = {success}. Details = {details}')
            except Exception as e:
                logger.error(f'Error in adding contact phone or email = {e}')
        else:
            logger.error(f"Unknown action for email: {email_data['message_id']}")
            success, details = False, "Unknown command. Please provide a valid action (Add, Update, Remove, Contact List)."

        logger.info(f"Details = : {details}")
        if success:
            email_obj = Email.objects.filter(id=email_data['email_id']).first()
            if email_obj:
                email_obj.is_processed = True
                email_obj.save()
        else:
            # TODO check here if in command there was Text or any other valid commands that are not in contact management
            pass

        self._construct_response_message(user_id=email_data['user_id'], success=success, details=details, message_id=email_data['message_id'], email_id=email_data['email_id'], bot=email_data['bot'])

    def _add_contact_email(self, email_data):
        """
        Add a contact email based on the email data.
        """
        name, email, _ = self._parse_contact_info(email_data)
        valid, message = self._validate_contact_details(name, email=email)
        if valid:
            contact, created = Contact.objects.get_or_create(user=email_data['user_id'], contact_name=name, defaults={'email': email})
            if created:
                return True, f"Contact email {email} added successfully."
            else:
                return True, f"Contact email {email} already exists."
        return False, message

    def _add_contact_number(self, email_data, phone_number):
        """
        Add a contact number based on the email data.
        """
        name, _, _ = self._parse_contact_info(email_data)
        valid, message = self._validate_contact_details(name, phone=phone_number)
        if valid:
            contact, created = Contact.objects.get_or_create(user=email_data['user_id'], contact_name=name, defaults={'phone_number': phone_number})
            if created:
                return True, f"Contact number {phone_number} added successfully."
            else:
                return True, f"Contact number {phone_number} already exists."
        return False, message

    def _update_contact_email(self, email_data):
        """
        Update a contact email based on the email data.
        """
        name, new_email, _ = self._parse_contact_info(email_data)
        valid, message = self._validate_contact_details(name, email=new_email)
        if valid:
            contact = Contact.objects.filter(user=email_data['user_id'], name=name).first()
            if contact:
                contact.email = new_email
                contact.save()
                return True, f"Contact email updated to {new_email}."
            else:
                return False, f"Contact {name} not found."
        return False, message

    def _update_contact_number(self, email_data, new_number):
        """
        Update a contact number based on the email data.
        """
        name, _, _ = self._parse_contact_info(email_data)
        valid, message = self._validate_contact_details(name, phone=new_number)
        if valid:
            contact = Contact.objects.filter(user=email_data['user_id'], name=name).first()
            if contact:
                contact.phone = new_number
                contact.save()
                return True, f"Contact number updated to {new_number}."
            else:
                return False, f"Contact {name} not found."
        return False, message

    def _remove_contact(self, email_data):
        """
        Remove a contact based on the email data.
        """
        name, _, _ = self._parse_contact_info(email_data)
        contact = Contact.objects.filter(user=email_data['user_id'], name=name).first()
        if contact:
            contact.delete()
            return True, f"Contact {name} removed successfully."
        else:
            return False, f"Contact {name} not found."

    def _contact_list(self, email_data):
        """
        Retrieve and prepare the contact list for the user.
        """
        contacts = Contact.objects.filter(user=email_data['user_id'])
        contact_list = "\n".join([f"{contact.name}: {contact.email if contact.email else contact.phone}" for contact in contacts])
        return True, contact_list

    def _parse_contact_info(self, email_data):
        """
        Parse contact name, email, and phone number from the email subject or body.
        Handles cases like "Add Contact Number +14024312303" and "Add Contact Email bd@gmail.com".
        """
        content = email_data['subject']

        # Detect and extract an email address
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', content)
        email = email_match.group(0) if email_match else None

        # Detect and extract a phone number (US phone numbers)
        phone_match = re.search(r'(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', content)
        phone = phone_match.group(0) if phone_match else None

        # Extract contact name: assume any word not part of a command, email, or phone number is the name
        # First, remove the found commands, phone numbers, and email from the content
        content_without_details = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '', content)  # Remove email
        content_without_details = re.sub(r'(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', '', content_without_details)  # Remove phone number
        content_without_details = re.sub(r'Add Contact (Email|Number)', '', content_without_details, flags=re.IGNORECASE)  # Remove the command, case-insensitive


        # Clean up extra spaces and consider the remaining content as the contact name
        name = content_without_details.strip()

        return name, email, phone

    def _validate_contact_details(self, name, email=None, phone=None):
        """
        Validate contact details.
        """
        if email and not self._validate_email(email):
            return False, "Invalid email address format."
        if phone and not self._validate_phone_number(phone):
            return False, "Invalid phone number format."
        if not name:
            return False, "Contact name is required."
        return True, ""

    def _validate_email(self, email):
        """
        Validate email format.
        """
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(email_regex, email) is not None

    def _validate_phone_number(self, phone):
        """
        Validate phone number format.
        """
        phone_regex = r'(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
        return re.match(phone_regex, phone) is not None

    def _construct_response_message(self, user_id, success, details, message_id, email_id, bot):
        """
        Send a response to the user.
        """
        logger.info(f"User {user_id} | Success: {success} | Details: {details} | Message ID: {message_id}")
        try:
            contact_management_message = ContactManagementResponseMessages.objects.create(
                user = user_id,
                bot = bot,
                email = Email.objects.filter(id=email_id).first(),
                message_id = message_id,
                response_content = details
            )
        except Exception as e:
            logger.error(f'An error occurred while creating contact management response message object. Exception =  {e}')
