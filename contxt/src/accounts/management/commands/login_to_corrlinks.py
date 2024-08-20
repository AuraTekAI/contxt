
from django.core.management.base import BaseCommand
from django.conf import settings

from curl_cffi import requests
from selectolax.lexbor import LexborHTMLParser
from requests_toolbelt import MultipartEncoder

import logging


logger = logging.getLogger('login')


class Command(BaseCommand):
    help = 'Log in to Corrlinks and return a session object.'

    def handle(self, *args, **options):
        session = login_to_corrlinks()
        if session:
            logger.info("Session initialized successfully.")
            self.stdout.write("Session initialized successfully.")
        else:
            logger.error("Failed to initialize session.")
            self.stderr.write("Failed to initialize session.")

def login_to_corrlinks():
    """
    Logs into the Corrlinks website and returns a session object.
    Returns:
    - requests.Session or None: A session object if login is successful, None otherwise
    """
    try:
        req = requests.Session()
        req.headers.update({
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
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
        logger.info(f'http {http_ip_response.json()['origin']}')
        https_ip_response = req.get(settings.HTTPBIN_IP_URL_HTTPS)
        logger.info(f'https { https_ip_response.json()['origin']}')

        # Attempt to log in
        while True:
            r = req.get(settings.LOGIN_PAGE)
            if r.status_code == 200:
                logger.info(f"Login page fetched successfully: STATUS CODE = {r.status_code}")
                break
            logger.error("Login Page not feteched. Failed. Retrying ........")
            req.headers.clear()
            req.cookies.clear()
    
        # Parse hidden fields and update data
        soup = LexborHTMLParser(r.content)
        data = {
            settings.LOGIN_EMAIL_FIELD_ID : settings.USERNAME,
            settings.LOGIN_PASSWORD_FIELD_ID : settings.PASSWORD,
            settings.LOGIN_BUTTON_ID : settings.LOGIN_BUTTON_TEXT
        }
        data.update({x.attrs['name']: x.attrs['value'] for x in soup.css('input[type="hidden"]')})
        form = MultipartEncoder(fields=data)
        req.headers.update({'Content-Type': form.content_type})
        
        r = req.post(settings.LOGIN_PAGE, data=form.to_string())
        
        logger.info(f"Login attempt response: STATUS CODE = {r.status_code}")
        if r.status_code == 200:
            return req
        else:
            logger.error("Login attempt failed. Returning None.")
            return None
        
    except Exception as e:
        logger.error(f"An error occurred during login: {e}")
        return None