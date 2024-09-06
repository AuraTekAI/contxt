
from accounts.utils import get_username_password

from django.conf import settings

from curl_cffi import requests
from selectolax.lexbor import LexborHTMLParser
from requests_toolbelt import MultipartEncoder

import logging

logger = logging.getLogger('login')

class SessionManager:
    """
    Manages a single session for interacting with the Corrlinks website, including handling
    login and session management.

    Attributes:
    - _session (requests.Session, optional): A class-level attribute that holds the session instance.
      It is initialized to `None` and set during the first call to `get_session()`.

    Methods:
    - get_session(cls, bot_id, is_accept_invite=False):
        Retrieves the current session for the specified bot. If no session exists, initializes a
        new session by logging in with the credentials associated with the given `bot_id`.

        Args:
            bot_id (str): The bot ID used to fetch the appropriate credentials.
            is_accept_invite (bool, optional): A flag to indicate if the session is for accepting an invite.
                                               Defaults to False.

        Returns:
            requests.Session: The session object for interacting with the Corrlinks website.
            If login fails, `None` is returned.

    - _login_to_corrlinks(cls, bot_id, is_accept_invite=False):
        Handles the login process to the Corrlinks website using credentials associated with the
        specified `bot_id`. This includes sending login credentials, managing headers, handling
        proxies, and parsing hidden form fields.

        This method performs the following steps:
        1. Retrieves login credentials using `get_username_password(bot_id)`.
        2. Configures the session, including setting headers and proxies if needed.
        3. Fetches the login page and parses hidden form fields.
        4. Submits the login form with credentials and additional hidden fields.

        Args:
            bot_id (str): The bot ID used to fetch the appropriate credentials.
            is_accept_invite (bool, optional): A flag to indicate if the session is for accepting an invite.
                                               Defaults to False.

        Returns:
            requests.Session: The session object if login is successful.
            None: If login fails or an error occurs.
    """

    _session = None

    @classmethod
    def get_session(cls, bot_id, is_accept_invite=False):
        """
        Retrieves the current session for the specified bot. If no session exists, initializes a
        new session by logging in with the credentials associated with the given `bot_id`.

        Args:
            bot_id (str): The bot ID used to fetch the appropriate credentials.
            is_accept_invite (bool, optional): A flag to indicate if the session is for accepting an invite.
                                               Defaults to False.

        Returns:
            requests.Session: The session object for interacting with the Corrlinks website.
            If login fails, `None` is returned.
        """
        if cls._session is None:
            cls._session = cls._login_to_corrlinks(bot_id, is_accept_invite=is_accept_invite)
        return cls._session

    @classmethod
    def _login_to_corrlinks(cls, bot_id, is_accept_invite=False):
        """
        Handles the login process to the Corrlinks website using credentials associated with the
        specified `bot_id`.

        This method performs the following steps:
        1. Retrieves login credentials using `get_username_password(bot_id, is_accept_invite)`.
        2. Configures the session, including setting headers and proxies if needed.
        3. Fetches the login page and parses hidden form fields.
        4. Submits the login form with credentials and additional hidden fields.
        5. Returns the session object if login is successful or `None` if it fails.

        Args:
            bot_id (str): The bot ID used to fetch the appropriate credentials.
            is_accept_invite (bool, optional): A flag to indicate if the session is for accepting an invite.
                                               Defaults to False.

        Returns:
            requests.Session: The session object if login is successful.
            None: If login fails or an error occurs.
        """
        try:
            # Retrieve credentials
            user_name, password = get_username_password(bot_id=bot_id, is_accept_invite=is_accept_invite)
            logger.info(f'Credentials = {user_name} ____ {password}')
            req = requests.Session()
            req.headers.update({
                'User-Agent': settings.LOGIN_REQUEST_HEADER
            })

            # Configure proxies if specified
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

            # Fetch the login page
            while True:
                r = req.get(settings.LOGIN_PAGE)
                if r.status_code == 200:
                    logger.info(f"Login page fetched successfully: STATUS CODE = {r.status_code}")
                    break
                logger.error("Login Page not fetched. Retrying ........")
                req.headers.clear()
                req.cookies.clear()

            # Parse hidden fields and prepare login data
            soup = LexborHTMLParser(r.content)
            data = {
                settings.LOGIN_EMAIL_FIELD_ID: user_name,
                settings.LOGIN_PASSWORD_FIELD_ID: password,
                settings.LOGIN_BUTTON_ID: settings.LOGIN_BUTTON_TEXT
            }
            data.update({x.attrs['name']: x.attrs['value'] for x in soup.css('input[type="hidden"]')})
            form = MultipartEncoder(fields=data)
            req.headers.update({'Content-Type': form.content_type})

            # Submit the login form
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
