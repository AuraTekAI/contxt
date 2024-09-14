from contxt.utils.constants import MESSAGES
from django.core.management.base import BaseCommand
from core.models import ResponseMessages

class Command(BaseCommand):
    """
    This Django management command populates the ContactManagementResponseMessages model
    with predefined messages stored in the MESSAGES constant.

    The command either creates new messages or updates existing ones based on their message key.
    This ensures that all predefined response messages are stored or updated in the database.
    """

    help = "Populate ContactManagementResponseMessages model with predefined messages."

    def handle(self, *args, **kwargs):
        """
        The handle method is the main entry point for the command.

        It iterates through the MESSAGES constant, checking if each message key
        already exists in the ContactManagementResponseMessages model. If the message exists,
        it updates the response content; if it does not, it creates a new entry.

        Success and error messages are printed to the console during the execution.
        """
        try:
            # Loop through the predefined MESSAGES dictionary
            for message_key, message_data in MESSAGES.items():
                # Update or create the message entry in the database based on the message key
                message, created = ResponseMessages.objects.update_or_create(
                    message_key=message_key,
                    defaults={
                        'response_content': message_data['content']  # Set the content of the message
                    }
                )
                if created:
                    # If the message was created, print a success message
                    self.stdout.write(self.style.SUCCESS(f'Successfully created message: {message_key}'))
                else:
                    # If the message already existed and was updated, print a success message
                    self.stdout.write(self.style.SUCCESS(f'Updated message: {message_key}'))

        except Exception as e:
            # Catch any exceptions during the process and print an error message
            self.stdout.write(self.style.ERROR(f"Error populating messages: {str(e)}"))
