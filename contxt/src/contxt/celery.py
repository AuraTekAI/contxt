from celery import Celery, Task

from django.conf import settings

import os
import logging

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contxt.settings')

# Initialize a Celery application named 'contxt'.
app = Celery('contxt')
# Configure Celery using settings from the Django configuration file under the 'CELERY' namespace.
app.config_from_object('django.conf:settings', namespace='CELERY')
# Set 'task_ack_late' to True to acknowledge tasks after they are executed.
app.task_ack_late = True

"""
Logger configuration for Celery.
This setup helps in debugging and monitoring Celery tasks by capturing warnings and errors in a specific log file.
"""
# Create a file handler for logging Celery messages to 'celery.log' in the specified log directory.
file_handler = logging.FileHandler(os.path.join(settings.LOG_DIR, 'celery.log'))
file_handler.setLevel(logging.WARNING)  # Set the logging level to WARNING.
# Define the format for the log messages including timestamp, process name, log level, and message.
formatter = logging.Formatter('{asctime} [{processName}] {levelname} {message}', style='{')
file_handler.setFormatter(formatter)
# Create a logger for Celery with the specified name and add the file handler to it.
celery_logger = logging.getLogger(__name__)
celery_logger.addHandler(file_handler)


class CustomExceptionHandler(Task):
    """
    Custom task class for handling exceptions in Celery tasks.
    This class overrides the 'on_failure' method to log detailed failure information.
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Log detailed information when a Celery task fails.

        Parameters:
        - exc: Exception raised during task execution.
        - task_id: ID of the failed task.
        - args: Positional arguments passed to the task.
        - kwargs: Keyword arguments passed to the task.
        - einfo: Exception info including traceback details.
        """
        celery_logger.error('\n\n------ Failed task information starts here ------')
        celery_logger.error(f'Task name: {self.name}')
        celery_logger.error(f'Exception: {exc}')
        celery_logger.error(f'Task ID: {task_id}')
        celery_logger.error(f'Args: {args} ---- Kwargs: {kwargs}')
        celery_logger.error(f'Exception info: {einfo}')
        celery_logger.error('\n\n------ Failed task information ends here ------ \n\n')

# Automatically discover tasks from all registered Django apps.
app.autodiscover_tasks()
