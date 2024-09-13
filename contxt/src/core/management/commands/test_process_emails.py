from django.core.management.base import BaseCommand
from process_emails.email_processing_service import EmailProcessingHandler

class Command(BaseCommand):
    help = "This is just to test the email processing module."

    def handle(self, *args, **kwargs):
        ins = EmailProcessingHandler(bot_id=5)
