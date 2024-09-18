from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "This is just to test the email processing module."

    def handle(self, *args, **kwargs):
        call_command('push_new_emails', bot_id=2, is_accept_invite=False, pic_name='VIRGINIA ISABEL FUENTES', message_content='Welcome email sent to you by ConTXT team')
