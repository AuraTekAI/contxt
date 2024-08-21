
from accounts.login_service import SessionManager
from process_emails.utils import convert_cookies_to_splash_format, get_messages_to_send_from_database, update_sms_processed_value
from contxt.utils.helper_functions import save_screenshots_to_local, get_lua_script_absolute_path

from django.core.management.base import BaseCommand
from django.conf import settings

import logging
import json
import sys

STATIC_COOKIES = settings.STATIC_COOKIES

logger = logging.getLogger('push_email')

class Command(BaseCommand):
    help = 'Run the push email process to send replies.'

    def handle(self, *args, **kwargs):
        session = SessionManager.get_session()
        if not session:
            logger.error("Failed to retrieve session.")
            return
        self.run_push_email(session=session)

    def capture_session_state(self, session):
        state = {
            'headers': dict(session.headers),
            'cookies': {k: v for k, v in session.cookies.items() if k not in STATIC_COOKIES}
        }
        logger.info("Captured session state:")
        logger.info(json.dumps(state, indent=2))
        return state

    def log_response_info(self, response, is_splash_response=False, retry_number=0):
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

    def send_email_reply(self, session, message_content, message_id, session_state):
        reply_url = f"https://www.corrlinks.com/NewMessage.aspx?messageId={message_id}&type=reply"

        lua_script_path = get_lua_script_absolute_path(relative_path='lua_scripts/send_email_reply.lua')
        with open(lua_script_path, 'r') as file:
            lua_script = file.read()
        headers = settings.HEADERS_FOR_PUSH_EMAIL_REQUEST
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
            'headers': headers,
            'cookies': cookie_header,
            'splash_cookies': splash_cookies
        }

        result = None
        request_success = False
        for retry_number in range(settings.MAX_EMAIL_REPLY_RETRIES):
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
                self.log_response_info(response=response, is_splash_response=True, retry_number=retry_number + 1)

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

    def run_push_email(self, session=None):
        if session == None:
            logger.error('Missing session information. Maybe there was an error in login ?')
            sys.exit(1)
        message_id_content = []

        if settings.TEST_MODE == True:
            message_id = "3735999911"
            message_content = "This is a test reply message sent from local. Please ignore these messages. Apologies for any inconvenience."
            message_id_content.append([None, message_id, message_content])
        else:
            message_id_content = get_messages_to_send_from_database(message_id_content=message_id_content)

        if not message_id_content:
            logger.info('No SMS messages found to process at the moment.')
            return "No SMS messages found to process at the moment."

        session_state = self.capture_session_state(session)

        for sms_data in message_id_content:
            sms_id, message_id, message_content = sms_data
            if message_id and message_content:
                success = self.send_email_reply(session=session, message_content=message_content, message_id=message_id, session_state=session_state)
            else:
                continue

            if success:
                if not settings.TEST_MODE == True:
                    status = update_sms_processed_value(sms_id=sms_id)
                    if status:
                        logger.info('SMS processed value updated successfully.')
                    else:
                        logger.error('An error occurred while updating SMS processed value.')
                logger.info(f"Email reply sent successfully  sms_id = {sms_id} message_id = {message_id}")
            else:
                logger.error(f"Failed to send email reply. sms_id = {sms_id} message_id = {message_id}. Check {logger.name}.log for details.")
        return f"Push email operation completed. Check {logger.name}.log for details."

