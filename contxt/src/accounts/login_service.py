
from django.conf import settings

from curl_cffi import requests
from selectolax.lexbor import LexborHTMLParser
from requests_toolbelt import MultipartEncoder

import logging

logger = logging.getLogger('login')

class SessionManager:
    _session = None

    @classmethod
    def get_session(cls):
        if cls._session is None:
            cls._session = cls._login_to_corrlinks()
        return cls._session

    @classmethod
    def _login_to_corrlinks(cls):
        try:
            req = requests.Session()
            req.headers.update({
                'User-Agent': settings.LOGIN_REQUEST_HEADER
            })

            if settings.USE_PROXY and settings.PROXY_URL:
                logger.info(f'Using proxies {settings.PROXY_URL}')
                req.proxies = {'http': settings.PROXY_URL, 'https': settings.PROXY_URL}
            else:
                logger.info('Continue Without Proxies.')

            req.impersonate = 'chrome'
            req.base_url = settings.BASE_URL

            # Verify IP masking by checking the external IP
            http_ip_response = req.get(settings.HTTPBIN_IP_URL_HTTP)
            logger.info(f'http {http_ip_response.json()["origin"]}')
            https_ip_response = req.get(settings.HTTPBIN_IP_URL_HTTPS)
            logger.info(f'https {https_ip_response.json()["origin"]}')

            # Attempt to log in
            while True:
                r = req.get(settings.LOGIN_PAGE)
                if r.status_code == 200:
                    logger.info(f"Login page fetched successfully: STATUS CODE = {r.status_code}")
                    break
                logger.error("Login Page not fetched. Retrying ........")
                req.headers.clear()
                req.cookies.clear()

            # Parse hidden fields and update data
            soup = LexborHTMLParser(r.content)
            data = {
                settings.LOGIN_EMAIL_FIELD_ID: settings.USERNAME,
                settings.LOGIN_PASSWORD_FIELD_ID: settings.PASSWORD,
                settings.LOGIN_BUTTON_ID: settings.LOGIN_BUTTON_TEXT
            }
            data.update({x.attrs['name']: x.attrs['value'] for x in soup.css('input[type="hidden"]')})
            form = MultipartEncoder(fields=data)
            req.headers.update({'Content-Type': form.content_type})

            r = req.post(settings.LOGIN_PAGE, data=form.to_string())

            logger.info(f"Login attempt response: STATUS CODE = {r.status_code}")
            if r.status_code == 200:
                logger.info('Session initialized successfully.')
                return req
            else:
                logger.error("Login attempt failed.")
                return None

        except Exception as e:
            logger.error(f"An error occurred during login: {e}")
            return None
