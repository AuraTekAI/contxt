import ctypes
import json
import os


path = os.path.abspath(os.path.dirname(__file__))

lib = ctypes.cdll.LoadLibrary(f'{path}\\fingerprint.dll')
req = lib.request
req.argtypes = [ctypes.c_char_p]
req.restype = ctypes.c_char_p


params = {
    "tlsClientIdentifier": "chrome_126",
    "followRedirects": True,
    "insecureSkipVerify": False,
    "withoutCookieJar": False,
    "withDefaultCookieJar": False,
    "isByteRequest": False,
    "forceHttp1": False,
    "withDebug": False,
    "catchPanics": False,
    "withRandomTLSExtensionOrder": False,
    "timeoutSeconds": 30,
    "timeoutMilliseconds": 0,
    "sessionId": "my-session-id",
    "proxyUrl": "",
    "isRotatingProxy": False,
    "certificatePinningHosts": {},
    "headers": {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.5",
        "accept-encoding": "gzip, deflate, br, zstd",
        'upgrade-insecure-requests': '1',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'priority': 'u=1',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'te': 'trailers'
    },
    "headerOrder": [
        "user-agent",
        "accept",
        "accept-language",
        "accept-encoding",
        'upgrade-insecure-requests',
        'sec-fetch-dest',
        'sec-fetch-mode',
        'sec-fetch-site',
        'sec-fetch-user',
        'priority',
        'pragma',
        'cache-control',
        'te'
    ],
    "requestUrl": "https://www.corrlinks.com/Login.aspx",
    "requestMethod": "GET",
    "requestBody": "",
    "requestCookies": []
}
r = req(json.dumps(params).encode('utf-8'))
r_by = ctypes.string_at(r)
r_st = r_by.decode('utf-8')
f_res = json.loads(r_st)


print("Response", f_res['status'])
with open('response.html', 'w', encoding='utf-8') as f:
    f.write(f_res['body'])
