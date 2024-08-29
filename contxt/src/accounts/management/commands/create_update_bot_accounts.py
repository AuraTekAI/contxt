from accounts.models import BotAccount

from django.core.management.base import BaseCommand
from django.conf import settings

from django_celery_beat.models import PeriodicTask

import json
import os

class Command(BaseCommand):
    """
    A Django management command to sync bot accounts from a JSON configuration file.
    The command updates or creates bot accounts in the database based on the provided
    configuration file and syncs the bot's status with corresponding Celery Beat tasks.
    """

    help = 'Sync bot accounts from a JSON configuration file'

    def add_arguments(self, parser):
        """
        Adds custom command-line arguments to the command.
        In this case, a '--config-file' argument is added to specify the path
        to the JSON configuration file.
        """
        parser.add_argument(
            '--config-file',
            type=str,
            help='Path to the JSON configuration file'
        )

    def handle(self, *args, **kwargs):
        """
        The main method that gets executed when the command is run.
        This method performs the following steps:
        1. Determines the path to the JSON configuration file.
        2. Loads bot configurations from the JSON file.
        3. Syncs the bot accounts in the database with the configurations.
        4. Updates the status of Celery Beat tasks based on the bot's activity status.
        5. Disables and deactivates any bots that are in the database but not in the configuration file.
        """

        # Step 1: Determine the path to the JSON configuration file
        config_file_path = kwargs['config_file']

        # If no config file path is provided, use the default path
        if not config_file_path:
            # Move up one directory from BASE_DIR (which is `src`) and set the file path
            config_file_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'bot-accounts.json')
            print(f'Config file path = {config_file_path}')

        # Step 2: Load bot configurations from the JSON file
        with open(config_file_path, 'r') as file:
            bot_configs = json.load(file)

        # Create a set of bot emails from the configuration file for easy lookup
        configured_bot_emails = {bot['email'] for bot in bot_configs['bots']}

        # Retrieve all existing bots from the database
        existing_bots = BotAccount.objects.all()
        # Create a set of existing bot email addresses
        existing_bot_names = {bot.email_address for bot in existing_bots}

        # Step 3: Sync the bot accounts in the database with the configurations
        for bot_config in bot_configs['bots']:
            # Update or create the bot account based on the email address
            bot, created = BotAccount.objects.update_or_create(
                email_address=bot_config['email'],
                defaults={
                    'bot_name': bot_config['name'],
                    'email_password': bot_config['email_password'],
                    'corrlinks_password' : bot_config['corrlinks_password'],
                    'is_active' : bot_config['is_active']
                }
            )

            # Output the result of the update or creation process
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created bot: {bot_config["name"]}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated bot: {bot_config["name"]}'))

            # Step 4: Update the corresponding Celery Beat task's enabled status
            periodic_task_for_bot = PeriodicTask.objects.filter(args__contains=[bot.id]).first()
            if periodic_task_for_bot:
                periodic_task_for_bot.enabled = bot.is_active
                periodic_task_for_bot.save()

        # Step 5: Identify and deactivate bots that are in the database but not in the configuration file
        missing_bots = existing_bot_names - configured_bot_emails
        if missing_bots:
            for missing_bot in missing_bots:
                bot_obj = BotAccount.objects.filter(email_address=missing_bot).first()
                if bot_obj:
                    # Disable the corresponding Celery Beat task
                    periodic_task_for_bot = PeriodicTask.objects.filter(args__contains=[bot_obj.id]).first()
                    if periodic_task_for_bot:
                        periodic_task_for_bot.enabled = False
                        periodic_task_for_bot.save()

                    # Deactivate the bot in the database
                    bot_obj.is_active = False
                    bot_obj.save()

                # Output a warning for each missing bot
                self.stdout.write(self.style.WARNING(f'Bot missing in config file: {missing_bot}. Its is_active value has been set to False.'))
        else:
            # Output a success message if all bots are present in the configuration file
            self.stdout.write(self.style.SUCCESS('All bots in the database are present in the configuration file.'))
