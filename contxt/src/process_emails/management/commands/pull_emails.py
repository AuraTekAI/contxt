from accounts.login_service import SessionManager

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command

from selectolax.lexbor import LexborHTMLParser
from requests_toolbelt import MultipartEncoder

import re
import logging


logger = logging.getLogger('pull_email')


HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.5',
    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    'X-MicrosoftAjax': 'Delta=true',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Referer': 'INBOX_URL'
}

class Command(BaseCommand):
    help = 'Process unread emails from the Corrlinks inbox'

    def handle(self, *args, **options):
        # Retrieve session from another command
        logger.info('Fetching session via Login service...')

        session = SessionManager.get_session()
        if not session:
            logger.error("Failed to retrieve session.")
            return
