
from accounts.login_service import SessionManager
from process_emails.utils import convert_cookies_to_splash_format, get_messages_to_send_from_database, update_sms_processed_value
from contxt.utils.helper_functions import save_screenshots_to_local, get_lua_script_absolute_path
from contxt.utils.constants import CURRENT_TASKS_RUN_BY_BOTS

from django.core.management.base import BaseCommand
from django.conf import settings

import logging
import json
import sys

STATIC_COOKIES = settings.STATIC_COOKIES



class Command(BaseCommand):
    """
    Django management command to process and send email replies based on data retrieved from the database.

    Attributes:
        help (str): Description of the command's purpose.

    Methods:
        handle(*args, **kwargs):
            Entry point for the command. Retrieves a session and initiates the push email process.

        capture_session_state(session):
            Captures and logs the current state of the session including headers and cookies.

        log_response_info(response, is_splash_response=False, retry_number=0):
            Logs detailed information about the response from the email reply request.

        send_email_reply(session, message_content, message_id, session_state):
            Sends an email reply using a Splash service and handles retry logic.

        run_push_email(session=None):
            Main method to handle the push email process including retrieving messages and sending replies.
    """
    help = 'Run the push email process to send replies.'
    command_name = CURRENT_TASKS_RUN_BY_BOTS['push_emails']

    def add_arguments(self, parser):
        parser.add_argument('--message_id', type=str, help='The ID of the message (optional).')
        parser.add_argument('--message_content', type=str, help='The content of the message (optional).')
        parser.add_argument('--bot_id', type=int, help='The bot id for the bot executing tasks.')

    def handle(self, *args, **kwargs):
        """
        Executes the command to send email replies.

        This method retrieves a session from `SessionManager` and then calls `run_push_email` to process and send replies.

        Args:
            *args: Positional arguments (not used).
            **kwargs: Keyword arguments (not used).

        Returns:
            None
        """

        message_id = kwargs.get('message_id')
        message_content = kwargs.get('message_content')
        bot_id = kwargs.get('bot_id')

        if bot_id:
            logger = logging.getLogger(f'bot_{bot_id}_{self.command_name}')
        else:
            logger = logging.getLogger('push_email')

        logger.info(f'Push Email got bot id = {bot_id} ')

        session = SessionManager.get_session(bot_id=bot_id)
        if not session:
            logger.error(f"Failed to retrieve session for bot = {bot_id}.")
            return
        self.run_push_email(session=session, message_id=message_id, message_content=message_content, bot_id=bot_id, logger=logger)

    def capture_session_state(self, session, logger):
        """
        Captures and logs the current state of the session.

        This includes the session headers and cookies, excluding static cookies defined in settings.

        Args:
            session (requests.Session): The session object to capture state from.

        Returns:
            dict: A dictionary containing the captured session headers and cookies.
        """
        state = {
            'headers': dict(session.headers),
            'cookies': {k: v for k, v in session.cookies.items() if k not in STATIC_COOKIES}
        }
        logger.info("Captured session state:")
        logger.info(json.dumps(state, indent=2))
        return state

    def log_response_info(self, response, is_splash_response=False, retry_number=0, logger=None):
        """
        Logs detailed information about the HTTP response.

        This includes URL, status code, headers, cookies, and body content. If the response is from Splash, it logs additional details.

        Args:
            response (requests.Response): The response object to log.
            is_splash_response (bool): Indicates if the response is from Splash.
            retry_number (int): The retry attempt number.

        Returns:
            None
        """
        logger.info(f"=== RESPONSE INFO ===")
        logger.info(f"URL: {response.url}")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Headers: {json.dumps(dict(response.headers), indent=2)}")
        logger.info(f"Cookies: {json.dumps(dict(response.cookies), indent=2)}")

        if is_splash_response:
            json_response = response.json()
            html_content = json_response.get('html')
            logger.info(f"Response Body: {response.text[:1000]}")
            if html_content is not None:
                with open(f"response_content_{response.status_code}_try{retry_number}.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
            else:
                logger.error(f"Empty HTML page returned. {response.url} {response.status_code}")
        else:
            logger.info(f"Response Body: {response.text[:1000]}")
            with open(f"response_content_{response.status_code}_try{retry_number}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
        logger.info(f"=====================")

    def send_email_reply(self, session, message_content, message_id, session_state, logger):
        """
        Sends an email reply using the Splash service.

        Constructs a POST request with Lua script and session data, then handles retries for sending the reply.

        Args:
            session (requests.Session): The session object to use for sending the reply.
            message_content (str): The content of the reply message.
            message_id (str): The ID of the message to reply to.
            session_state (dict): The current state of the session including headers and cookies.

        Returns:
            bool: True if the reply was sent successfully, False otherwise.
        """
        reply_url = f"https://www.corrlinks.com/NewMessage.aspx"

        lua_script_path = get_lua_script_absolute_path(relative_path='lua_scripts/send_new_emails.lua')
        with open(lua_script_path, 'r') as file:
            lua_script = file.read()
        headers = settings.HEADERS_FOR_NEW_EMAIL_REQUEST
        cookies = session_state['cookies']

        splash_cookies = []
        splash_cookies = convert_cookies_to_splash_format(splash_cookies=splash_cookies, cookies=cookies)
        if splash_cookies is False:
            logger.error(f'Error occurred while converting cookies to splash browser format. \
            This is what was returned by the |convert_cookies_to_splash_format| function. {splash_cookies}')
            return False

        cookie_header = "; ".join([f"{key}={value}" for key, value in cookies.items()])

        params = {
            'lua_source': lua_script,
            'message_content': message_content,
            'reply_url': reply_url,
            'pic_number' : '09527510',
            'headers': headers,
            'cookies': cookie_header,
            'splash_cookies': splash_cookies
        }

        result = None
        request_success = False
        for retry_number in range(settings.MAX_NEW_EMAIL_RETRIES):
            response = session.post(settings.SPLASH_URL, json=params)
            result = response.json()

            if not settings.TEST_MODE :
                result.pop('html', None)
            logger.info(f'Request results = {result}')

            if settings.TEST_MODE:
                """
                For saving screenshots to local for debugging,
                please make sure they have word screenshot in their key value.
                """
                save_screenshots_to_local(result=result, logger_name=logger.name)
                self.log_response_info(response=response, is_splash_response=True, retry_number=retry_number + 1, logger=logger)

            if response.status_code == 200 and result['element_found'] and result['text_box_message'] != 'Text box not found':
                request_success = True
                break

        if response.status_code == 200 and request_success:
            logger.info('Reply sent successfully.')
            logger.info('----------------------------------')
            return True

        logger.error(f'Something went wrong in send_reply_email.')
        logger.error('----------------------------------')
        return False

    def run_push_email(self, session=None, message_id=None, message_content=None, bot_id=None, logger=None):
        """
        Runs the push email process, retrieving messages from the database and sending replies.

        Handles test mode and updates the SMS processed value after sending each reply.

        Args:
            session (requests.Session): The session object to use for sending replies.

        Returns:
            str: A status message indicating the completion of the push email operation.
        """
        if session == None:
            logger.error('Missing session information. Maybe there was an error in login ?')
            sys.exit(1)
        message_id_content = []

        if settings.TEST_MODE == True:
            message_id = "3735999911"
            message_content = "This is a test reply message sent from local. Please ignore these messages. Apologies for any inconvenience."
            message_id_content.append([None, message_id, message_content])
        elif message_id and message_content:
            message_id_content.append([None, message_id, message_content])
        else:
            message_id_content = get_messages_to_send_from_database(message_id_content=message_id_content, bot_id=bot_id)

        if not message_id_content:
            logger.info('No SMS messages found to process at the moment.')
            return "No SMS messages found to process at the moment."

        session_state = self.capture_session_state(session, logger=logger)

        for sms_data in message_id_content:
            sms_id, message_id, message_content = sms_data
            if message_id and message_content:
                success = self.send_email_reply(session=session, message_content=message_content, message_id=message_id, session_state=session_state, logger=logger)
            else:
                continue

            if success:
                if not settings.TEST_MODE == True and not sms_id == None:
                    status = update_sms_processed_value(sms_id=sms_id)
                    if status:
                        logger.info('SMS processed value updated successfully.')
                    else:
                        logger.error('An error occurred while updating SMS processed value.')
                logger.info(f"Email reply sent successfully  sms_id = {sms_id} message_id = {message_id}")
                logger.info("------------------------------------------------------")
            else:
                logger.error(f"Failed to send email reply. sms_id = {sms_id} message_id = {message_id}. Check {logger.name}.log for details.")
                logger.info("------------------------------------------------------")
        return f"Push email operation completed. Check {logger.name}.log for details."

