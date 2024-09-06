from curl_cffi import requests
from selectolax.lexbor import LexborHTMLParser
from requests_toolbelt import MultipartEncoder
import os
import ctypes


data = {
    'ctl00$mainContentPlaceHolder$loginUserNameTextBox': "info@contxts.net",
    'ctl00$mainContentPlaceHolder$loginPasswordTextBox': "ConTXTsR0ck$",
    'ctl00$mainContentPlaceHolder$loginButton': 'Login >>'
}


def main():
    with requests.Session() as req:
        req.impersonate = 'chrome'
        req.base_url = 'https://www.corrlinks.com/'
        while True:
            try:
                r = req.get('Login.aspx')
                if r.status_code == 200:
                    break
                print('retrying failed request...')
                req.headers.clear()
                req.cookies.clear()
            except requests.RequestsError:
                continue
        print(r)
        soup = LexborHTMLParser(r.content)
        data.update({
            x.attrs['name']: x.attrs['value']
            for x in soup.css('input[type="hidden"]')
        })
        form = MultipartEncoder(data)
        req.headers.update({
            'Content-Type': form.content_type
        })
        r = req.post('Login.aspx', data=form.to_string())
        print(r)
        r = req.get('Inbox.aspx')
        print(r)
        with open('r.html', 'w', encoding='utf-8') as f:
            f.write(r.text)


if __name__ == "__main__":
    path = os.path.abspath(os.path.dirname(__file__))
    ctypes.cdll.LoadLibrary(f'{path}\\fingerprint.dll')
    main()
