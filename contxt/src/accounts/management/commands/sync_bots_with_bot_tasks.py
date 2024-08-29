
from accounts.models import BotAccount

from django.core.management.base import BaseCommand

from django_celery_beat.models import PeriodicTask

class Command(BaseCommand):
    # A brief description of what this command does
    help = 'Sync bot accounts to their celery beat tasks from database tables'

    def handle(self, *args, **kwargs):
        """
        The main method that gets executed when the command is run.
        This method performs the following steps:
        1. Retrieves all bot accounts from the database.
        2. Iterates over each bot account to find the corresponding periodic task.
        3. If a periodic task is found, it updates the task's 'enabled' status
           based on the bot's 'is_active' status.
        4. Saves the changes to the database and outputs the result.
        """

        # Step 1: Retrieve all bot accounts from the database
        bot_accounts = BotAccount.objects.all()

        # Step 2: Iterate over each bot account
        for bot in bot_accounts:
            """
            Step 3: For each bot account, filter the PeriodicTask model to find the first
            periodic task where the bot's ID is included in the 'args' field.
            This assumes 'args' is stored as a JSON-encoded list and the bot's ID
            is part of that list.
            """
            periodic_task_for_bot = PeriodicTask.objects.filter(args__contains=[bot.id]).first()

            # Step 4: Check if a corresponding periodic task was found
            if periodic_task_for_bot:
                """
                If a periodic task is found, update its 'enabled' field to match
                the bot's 'is_active' status. This will ensure that the periodic task
                is only enabled when the bot is active.
                """
                periodic_task_for_bot.enabled = bot.is_active

                # Save the updated task back to the database
                periodic_task_for_bot.save()

                # Output the success message to the console
                self.stdout.write(
                    self.style.SUCCESS(f'Bot_{bot.id} periodic task value set to {periodic_task_for_bot.enabled}.')
                )
