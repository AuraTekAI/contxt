## login.py ##

from curl_cffi import requests
from selectolax.lexbor import LexborHTMLParser
from requests_toolbelt import MultipartEncoder
import os
import logging
import ctypes
from variables import *

def login_to_corrlinks():
    try:
        path = os.path.abspath(os.path.dirname(__file__))
        ctypes.cdll.LoadLibrary(f'{path}\\{FINGERPRINT_DLL}')
        
        req = requests.Session()  # Initialize session here
        #req.headers.update({
        #    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        #})

        if USE_PROXY and PROXY_URL:
            req.proxies = {'http': PROXY_URL, 'https': PROXY_URL}

        req.impersonate = 'chrome'
        req.base_url = BASE_URL
    
        # Verify IP masking by checking the external IP
        http_ip_response = req.get(HTTPBIN_IP_URL_HTTP)
        print('http', http_ip_response.json()['origin'])
        https_ip_response = req.get(HTTPBIN_IP_URL_HTTPS)
        print('https', https_ip_response.json()['origin'])

        # Attempt to log in
        while True:
            r = req.get(LOGIN_PAGE)
            if r.status_code == 200:
                print("Login page fetched successfully:", r.status_code)
                break
            print('retrying failed request...')
            req.headers.clear()
            req.cookies.clear()
    
        # Parse hidden fields and update data
        soup = LexborHTMLParser(r.content)
        data = {
            'ctl00$mainContentPlaceHolder$loginUserNameTextBox': USERNAME,
            'ctl00$mainContentPlaceHolder$loginPasswordTextBox': PASSWORD,
            'ctl00$mainContentPlaceHolder$loginButton': LOGIN_BUTTON_TEXT
        }
        data.update({x.attrs['name']: x.attrs['value'] for x in soup.css('input[type="hidden"]')})
        form = MultipartEncoder(fields=data)
        req.headers.update({'Content-Type': form.content_type})
        r = req.post(LOGIN_PAGE, data=form.to_string())
        print("Login attempt response:", r.status_code)

        # if r.status_code == 200:
        #     r = req.get(INBOX_PAGE)
        #     print("Accessed Inbox Page:", r.status_code)
        #     with open('r.html', 'w', encoding='utf-8') as f:
        #         f.write(r.text)
        #     print("Saved inbox content to r.html")

        return req  # Return the session object for further use
    except Exception as e:
        logging.error(f"An error occurred during login: {e}")
        return None  # It might be safer to return None or handle this more gracefully

if __name__ == "__main__":
    session = login_to_corrlinks()
    if session:
        print("Session initialized successfully.")
    else:
        print("Failed to initialize session.")
