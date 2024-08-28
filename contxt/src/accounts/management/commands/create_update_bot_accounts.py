
from accounts.models import BotAccount

from django.core.management.base import BaseCommand
from django.conf import settings

import json
import os

class Command(BaseCommand):
    help = 'Sync bot accounts from a JSON configuration file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config-file',
            type=str,
            help='Path to the JSON configuration file'
        )

    def handle(self, *args, **kwargs):
        config_file_path = kwargs['config_file']

        if not config_file_path:
            # Move up one directory from BASE_DIR (which is `src`)
            config_file_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'bot-accounts.json')
            print(f'Config file path = {config_file_path}')

        with open(config_file_path, 'r') as file:
            bot_configs = json.load(file)

        configured_bot_emails = {bot['email'] for bot in bot_configs['bots']}

        existing_bots = BotAccount.objects.all()
        existing_bot_names = {bot.email_address for bot in existing_bots}

        for bot_config in bot_configs['bots']:
            bot, created = BotAccount.objects.update_or_create(
                email_address=bot_config['email'],
                defaults={
                    'bot_name': bot_config['name'],
                    'email_password': bot_config['email_password'],
                    'corrlinks_password' : bot_config['corrlinks_password'],
                    'is_active' : bot_config['is_active']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created bot: {bot_config["name"]}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated bot: {bot_config["name"]}'))

        missing_bots = existing_bot_names - configured_bot_emails
        if missing_bots:
            for missing_bot in missing_bots:
                bot_obj = BotAccount.objects.filter(email_address=missing_bot).first()
                if bot_obj:
                    bot_obj.is_active = False
                    bot_obj.save()
                self.stdout.write(self.style.WARNING(f'Bot missing in config file: {missing_bot}. Its is_active value has been set to False.'))
        else:
            self.stdout.write(self.style.SUCCESS('All bots in the database are present in the configuration file.'))
