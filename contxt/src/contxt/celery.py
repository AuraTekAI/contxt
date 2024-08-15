from celery import Celery, Task

from django.conf import settings

import os
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contxt.settings')


app = Celery('contxt')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.task_ack_late = True

"""
Defining logger for celery here because of the issue of circular imports
All logs for celery are written in logs/celery.log file
"""
file_handler = logging.FileHandler(os.path.join(settings.LOG_DIR, 'celery.log'))
file_handler.setLevel(logging.WARNING)
formatter = logging.Formatter('{asctime} [{processName}] {levelname} {message}', style='{')
file_handler.setFormatter(formatter)
celery_logger = logging.getLogger(__name__)
celery_logger.addHandler(file_handler)


class CustomExceptionHandler(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        celery_logger.error('\n\n------ Failed task information starts here ------')
        celery_logger.error(f'Task name: {self.name}')
        celery_logger.error(f'Exception: {exc}')
        celery_logger.error(f'Task ID: {task_id}')
        celery_logger.error(f'Args: {args} ---- Kwargs: {kwargs}')
        celery_logger.error(f'Exception info: {einfo}')
        celery_logger.error('\n\n------ Failed task information ends here ------ \n\n')


app.autodiscover_tasks()