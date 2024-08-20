import logging
import json
from django.core.management.base import BaseCommand

from login import login_to_corrlinks
from variables import MAX_EMAIL_REPLY_RETRIES, HEADERS_FOR_PUSH_EMAIL_REQUEST, SPLASH_URL, ENVIRONMENT
from utils.helper_functions import convert_cookies_to_splash_format, get_sms_replies_for_send_email, update_sms_processed_status

STATIC_COOKIES = {
    '__cflb': '02DiuJS4Qt1fYJgjizGYDpBdpvG3kZuePiK6aACa2VVk8',
    'cf_clearance': 'NVzVrHA955EqW3BWDz88iyjl3C9DgxYunr5aA39Ime0-1720556066-1.0.1.1-iRuayH1JZaLN0s7CorH6YLiiL6473CYJDarLnx57PclIoO3rJL1j_WVDVTzRamuBzuDeGSzZA8Hf4rj2BVzjZg'
}

logger = logging.getLogger('push_email')

class Command(BaseCommand):
    help = 'Run the push email process to send replies.'

    def handle(self, *args, **kwargs):
        self.run_push_email()

    def capture_session_state(self, session):
        state = {
            'headers': dict(session.headers),
            'cookies': {k: v for k, v in session.cookies.items() if k not in STATIC_COOKIES}
        }
        logger.info("Captured session state:")
        logger.info(json.dumps(state, indent=2))
        return state

    def update_session_state(self, session, state):
        session.headers.update(state['headers'])
        session.cookies.update(state['cookies'])
        session.cookies.update(STATIC_COOKIES)

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

        with open('utils/lua_scripts/send_email_reply.lua', 'r') as file:
            lua_script = file.read()
        headers = HEADERS_FOR_PUSH_EMAIL_REQUEST
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
        for retry_number in range(MAX_EMAIL_REPLY_RETRIES):
            response = session.post(SPLASH_URL, json=params)
            result = response.json()

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

    def run_push_email(self):
        message_id_content = []

        if ENVIRONMENT == 'TEST':
            message_id = "3735999911"
            message_content = "This is a test reply message sent from local. Please ignore these messages. Apologies for any inconvenience."
            message_id_content.append([None, message_id, message_content])
        else:
            message_id_content = get_sms_replies_for_send_email(message_id_content=message_id_content)

        if not message_id_content:
            logger.info('No SMS messages found to process at the moment.')
            return "No SMS messages found to process at the moment."

        session = login_to_corrlinks()
        if not session:
            logger.error("Failed to login to Corrlinks")
            return "Failed to login to Corrlinks"

        session_state = self.capture_session_state(session)

        for sms_data in message_id_content:
            sms_id, message_id, message_content = sms_data
            if message_id and message_content:
                success = self.send_email_reply(session=session, message_content=message_content, message_id=message_id, session_state=session_state)
            else:
                continue

            if success:
                if ENVIRONMENT != 'TEST':
                    status = update_sms_processed_status(sms_id=sms_id)
                    if status:
                        logger.info('SMS processed value updated successfully.')
                    else:
                        logger.error('An error occurred while updating SMS processed value.')
                logger.info(f"Email reply sent successfully  sms_id = {sms_id} message_id = {message_id}")
            else:
                logger.error(f"Failed to send email reply. sms_id = {sms_id} message_id = {message_id}. Check push_email_interaction.log for details.")
        return "Push email operation completed. Check push_email_interaction.log for details."

