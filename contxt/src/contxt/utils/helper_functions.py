
import logging
import base64
import os
import json

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
