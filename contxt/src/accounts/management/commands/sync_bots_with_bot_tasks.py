
from accounts.models import BotAccount

from django.core.management.base import BaseCommand
from django.conf import settings

from django_celery_beat.models import PeriodicTask, IntervalSchedule

import json

class Command(BaseCommand):
    help = 'Sync bot accounts to their celery beat tasks from database tables'

    def handle(self, *args, **kwargs):
        """
        The main method that gets executed when the command is run.
        This method performs the following steps:
        1. Retrieves all bot accounts from the database.
        2. Iterates over each bot account to find the corresponding periodic task.
        3. If a periodic task is found, it updates the task's 'enabled' status
           based on the bot's 'is_active' status.
        4. If no periodic task is found for an active bot, it creates a new periodic task.
        5. Saves the changes to the database and outputs the result.
        """

        # Step 1: Retrieve all bot accounts from the database
        bot_accounts = BotAccount.objects.all()

        # Step 2: Iterate over each bot account
        for bot in bot_accounts:
            periodic_task_for_bot = PeriodicTask.objects.filter(args__contains=[bot.id]).first()

            # Step 3: Check if a corresponding periodic task was found
            if periodic_task_for_bot:
                # Update the 'enabled' status based on the bot's 'is_active' status
                if periodic_task_for_bot.enabled != bot.is_active:
                    periodic_task_for_bot.enabled = bot.is_active
                    periodic_task_for_bot.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Bot_{bot.id} periodic task value set to {periodic_task_for_bot.enabled}.')
                )
            elif bot.is_active:
                # Step 4: Create a new periodic task if the bot is active and no task exists
                schedule, _ = IntervalSchedule.objects.get_or_create(
                    every=settings.BOT_TASK_INTERVAL_VALUE,  # Set the interval for the task, e.g., every 10 minutes
                    period=IntervalSchedule.MINUTES
                )

                PeriodicTask.objects.create(
                    interval=schedule,
                    name=f'BOT_{bot.id}_TASKS',
                    task='core.tasks.entrypoint_for_bots',
                    args=json.dumps([bot.id]),
                    enabled=True
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Created a new periodic task for Bot_{bot.id} and enabled it.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Bot_{bot.id} is inactive and no periodic task was created.')
                )
