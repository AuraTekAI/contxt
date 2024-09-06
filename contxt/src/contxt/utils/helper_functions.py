
from contxt.utils.constants import CURRENT_TASKS_RUN_BY_BOTS

from django.conf import settings

import logging
import base64
import os
import json

logger = logging.getLogger('django')

def extract_screenshots(data):
    """
    Extracts all values from a dictionary where the keys contain the word 'screenshot'.

    Parameters:
    - data (dict): The dictionary containing keys with names like 'screenshot_1', 'screenshot_2', etc.

    Returns:
    - list: A list of values corresponding to keys that contain the word 'screenshot'.
    """
    screenshots = []

    for key, value in data.items():
        if 'screenshot' in key:
            screenshots.append(value)

    return screenshots

def save_screenshots_to_local(result={}, logger_name='app'):
    """
    Saves screenshots and HAR data from the provided result to local files.

    This function extracts screenshots from the `result` dictionary, saves each screenshot as a PNG file
    in the local directory, and optionally saves HAR (HTTP Archive) data to a file.

    Parameters:
        result (dict): A dictionary containing the data with screenshots and optionally HAR data.
                       Expected to include base64-encoded screenshots and a 'har' key with HAR data.
        logger_name (str): The name of the logger to use for logging messages. Defaults to 'app'.

    Returns:
        bool: `True` if screenshots and HAR data were successfully saved; `None` if there were no screenshots to save.

    Logs:
        - Logs a message if there are no screenshots to save.
    """

    logger = logging.getLogger(logger_name)
    if result == {}:
        logger.info('No screenshots to save. Returning None.')
        return None

    screen_shots = extract_screenshots(result)
    screenshot_number = 1
    for screenshot in screen_shots:
        screenshot_name = f'screenshot_{screenshot_number}.png'
        with open(screenshot_name, 'wb') as f:
            f.write(base64.b64decode(screenshot))
            f.close()

        screenshot_number = screenshot_number + 1

    har_data = result.get('har', None)
    if har_data:
        with open('output.har', 'w') as f:
            json.dump(har_data, f)

    return True

def get_lua_script_absolute_path(relative_path):
    """
    Constructs the dynamic file path based on a relative path.

    Parameters:
    - relative_path (str): The relative path to the file from the script's location.

    Returns:
    - str: The dynamically generated absolute file path.
    """
    # Get the current script directory
    current_dir = os.path.dirname(__file__)

    # Construct the absolute path to the file
    file_path = os.path.join(current_dir, relative_path)

    return file_path

def update_logging_config():
    """
    Update the logging configuration based on bot data from a JSON file.

    This function performs the following steps:
    1. Loads the base logging configuration from the Django settings.
    2. Reads bot configuration data from a JSON file.
    3. Iterates over each bot and their associated tasks.
    4. For each bot and task, creates and adds a file handler and logger to the logging configuration.
    5. Applies the updated logging configuration using `logging.config.dictConfig`.
    """

    # Load the base logging configuration from Django settings
    logging_config = settings.LOGGING.copy()

    # Construct the path to the JSON file containing bot configurations
    config_file_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'bot-accounts.json')
    print(f'Config file path = {config_file_path}')

    # Open and read the JSON file containing bot configurations
    with open(config_file_path, 'r') as file:
        bot_configs = json.load(file)
        bots = bot_configs['bots']

    # Iterate over each bot in the bot configurations
    for bot in bots:
        # Convert the bot name to lowercase for consistency
        bot_name = bot['name'].lower()

        # Iterate over each task defined in CURRENT_TASKS_RUN_BY_BOTS
        for task_key, task_value in CURRENT_TASKS_RUN_BY_BOTS.items():
            # Define the filename for the log file based on bot name and task
            log_filename = os.path.join(settings.LOG_DIR, f'{bot_name}_{task_value}.log')

            # Define a file handler for the specific bot and task
            file_handler = {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': log_filename,
                'formatter': 'verbose',
            }

            # Generate a unique name for the file handler and add it to the configuration
            handler_name = f'{bot_name}_{task_value}_file'
            logging_config['handlers'][handler_name] = file_handler

            # Define a logger for the specific bot and task
            bot_logger_name = f'{bot_name}_{task_value}'
            bot_logger = {
                'handlers': ['console', handler_name],
                'level': 'DEBUG',
                'propagate': False,
            }

            # Add the logger to the logging configuration
            logging_config['loggers'][bot_logger_name] = bot_logger

    # Apply the updated logging configuration using the `dictConfig` method
    logging.config.dictConfig(logging_config)

