from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "This is just to make sure that scheduling stuff with beat scheduler implementation is correct"

    def handle(self, *args, **kwargs):
        print('I am running in celery.\n')
