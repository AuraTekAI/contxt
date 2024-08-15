import sys
import time

from django.core.management.base import BaseCommand, CommandParser
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "This command is used to block the container start up until the Database becomes available"

    def add_arguments(self, parser):
        parser.add_argument("--poll_seconds", type=float, default=3)
        parser.add_argument("--max_retries", type=int, default=10)

    def handle(self, *args, **options):
        max_retries = options['max_retries']
        poll_seconds = options['poll_seconds']

        for retry in range(max_retries):
            try:
                connection.ensure_connection()
            except OperationalError as ex:
                self.stdout.write(
                    "Database unavailable due to:"
                    " {error}".format(error=ex)
                )
                time.sleep(poll_seconds)
            else:
                break
        else:
            self.stdout.write(self.style.ERROR("Databse unavailable. Check the logs above for more information"))
            sys.exit(1)