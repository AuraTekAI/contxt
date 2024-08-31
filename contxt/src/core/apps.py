
from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class CoreConfig(AppConfig):
    """
    This is the application configuration class for the 'core' app.
    It contains configuration options and startup code that is run when the app is ready.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        """
        This method is called when the Django application is ready.
        It sets up the periodic tasks for bot accounts if Celery is enabled in the settings.
        """
        if settings.CELERY_ENABLED:  # Check if Celery is enabled in the settings
            # The following code sets up periodic tasks after migrations are applied

            @receiver(post_migrate)
            def setup_bot_periodic_tasks(sender, **kwargs):
                """
                This signal receiver function is executed after every migration.
                It creates periodic tasks for each active bot account in the database.
                """
                from accounts.models import BotAccount
                from django_celery_beat.models import PeriodicTask, IntervalSchedule
                import json

                # Create or get an existing interval schedule that runs every 10 minutes
                schedule, _ = IntervalSchedule.objects.get_or_create(
                    every=settings.BOT_TASK_INTERVAL_VALUE,
                    period=IntervalSchedule.MINUTES
                )

                # TODO: Re-evaluate the following line to ensure it fits your use case
                # Deletes all existing periodic tasks that have names starting with 'BOT_'
                PeriodicTask.objects.filter(name__startswith='BOT_').delete()

                # Iterate over all active bot accounts in the database
                for bot in BotAccount.objects.filter(is_active=True):
                    """
                    Create a new periodic task for each active bot.
                    Each task will run every 10 minutes and will trigger the
                    'core.tasks.entrypoint_for_bots' task with the bot's ID as an argument.
                    """
                    PeriodicTask.objects.create(
                        interval=schedule,
                        name=f'BOT_{bot.id}_TASKS',  # Name the task uniquely using the bot's ID
                        task='core.tasks.entrypoint_for_bots',  # Specify the task to run
                        args=json.dumps([bot.id])  # Pass the bot's ID as a JSON-encoded argument
                    )
