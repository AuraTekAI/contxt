## variables.py ##

import os
from twilio.rest import Client

# URL settings
LOGIN_URL = "https://www.corrlinks.com/Login.aspx"
INBOX_URL = "https://www.corrlinks.com/Inbox.aspx"
DEFAULT_URL = "https://www.corrlinks.com/Default.aspx"
UNREAD_MESSAGES_URL = "https://www.corrlinks.com/Inbox.aspx?UnreadMessages"
REPLY_URL_BASE = "https://www.corrlinks.com/NewMessage.aspx?messageId={message_id}&type=reply"
MESSAGE_PROCESSED = "https://www.corrlinks.com/MessageProcessed.aspx?type=send"
CONTACT_URL = "https://www.corrlinks.com/PendingContact.aspx"
TEST_REPLY_WEBHOOK_URL = "https://webhook.site/5eb549e9-09aa-4fe1-9bec-bcb5981d252a"
REPLY_WEBHOOK_URL = "https://smsreceiverapi.contxts.net/api/sms"
SMS_SEND_URL = 'https://textbelt.com/text'
SMS_STATUS_URL = 'https://textbelt.com/status/{}'
SMS_QUOTA_URL = 'https://textbelt.com/quota/{}'
SMS_RETRY_DELAY = 120  # seconds
MAX_SMS_RETRIES = 3

# Credentials for login
USERNAME = "bradleyaroth@gmail.com"
PASSWORD = "Thought20"
# USERNAME = "info@contxts.net"
# PASSWORD = "ConTXTsR0ck$"
LOGIN_BUTTON_TEXT = 'Login >>'

# Proxy settings
PROXY_URL = 'http://Glenna:r3orm8Ot2j=WmgJcO5@us.smartproxy.com:10000'

# URLs
BASE_URL = 'https://www.corrlinks.com/'
LOGIN_PAGE = 'Login.aspx'
INBOX_PAGE = 'Inbox.aspx'
HTTPBIN_IP_URL_HTTP = 'http://httpbin.org/ip'
HTTPBIN_IP_URL_HTTPS = 'https://httpbin.org/ip'

# Path to the DLL
FINGERPRINT_DLL = 'fingerprint.dll'

# Application behavior flags
CHECK_UNREAD_FLAG = True  # Flag to determine if unread messages should be checked
TEST_MODE = True  # Flag to enable test mode, which affects how emails are processed
USE_PROXY = False  # Flag to enable or disable proxy use during the login process

# Static MessageID for testing
STATIC_MESSAGE_ID = "3706018280"

# Database Connection Variables
DB_IP = "SQL1.reliantrack.local"
DB_USERNAME = "sa"
DB_PASSWORD = "Gr3@tSc0tch"
DB_NAME = "ConTXT"


# Consolidated Database Settings for import
DB_SETTINGS = {
    "postgres" : {
        "host": "localhost",
        "user": "postgres",
        "password": "123",
        "database": "contxt"
    },
    "default" : {
        "DB_IP": DB_IP,
        "DB_USERNAME": DB_USERNAME,
        "DB_PASSWORD": DB_PASSWORD,
        "DB_NAME": DB_NAME,
        "CONN_STR": f"DRIVER={{SQL Server}};SERVER={DB_IP};DATABASE={DB_NAME};UID={DB_USERNAME};PWD={DB_PASSWORD}"
    }
}

DB_TYPE = 'mssql'
ENVIRONMENT = 'DEV'

# SMS Auth
API_KEY = '3383a22f7ee0a5da47b11a90ce451b62df3cf185XVOK7QpjQSjJ2eNkHPSaQ9Jur'
TEST_TO_NUMBER = '4024312303'
TEST_KEY = '3383a22f7ee0a5da47b11a90ce451b62df3cf185XVOK7QpjQSjJ2eNkHPSaQ9Jur_test'
TEST_MESSAGE_BODY = 'Sending Test Message From ConTXT'
TEST_USER_ID = '15372010'

# BOT Email Account Credentials
EMAILURL0 = "mail.contxts.net"
EMIALURL1 = "smtp.gmail.com"
EMAIL0_USERNAME = "bradley@contxts.net"
EMAIL0_PASSWORD = "Gr3@tSc0tch"
EMAIL1_USERNAME = "skybluenook@gmail.com"
EMAIL1_PASSWORD = "dmfg oyct dcli qqru"
EMAIL2_USERNAME = "citylightpine@gmail.com"
EMAIL2_PASSWORD = "lnah gcme dqae rkxm"
EMAIL3_USERNAME = "goldenhourfly@gmail.com"
EMAIL3_PASSWORD = "qggm fcry sfiy yqvo"
EMAIL4_USERNAME = "coralreefglow@gmail.com"
EMAIL4_PASSWORD = "nnal grch rhni xzxb"
EMAIL5_USERNAME = "cloudninelight@gmail.com"
EMAIL5_PASSWORD = "mxdc hndy fgwm zgeu"

HEADERS_FOR_PUSH_EMAIL_REQUEST = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': "https://www.corrlinks.com/Inbox.aspx",
    'X-Requested-With': 'XMLHttpRequest',
    'X-MicrosoftAjax': 'Delta=true'
}
SPLASH_URL = 'http://localhost:8050/execute'
MAX_EMAIL_REPLY_RETRIES = 3
MAX_ACCEPT_INVITE_RETRIES = 3

MAIL_SEARCH_DAYS_VALUE = 7
MAIL_SEARCH_STRING = '(SUBJECT "Person in Custody:" SINCE '
MAIL_BROADER_SEARCH_STRING = '(SUBJECT "Custody" SINCE '

INVITATION_CODE_BOX_ID = 'ctl00_mainContentPlaceHolder_PendingContactUC1_InmateNumberTextBox'
INVITATION_CODE_GO_BUTTON_ID = 'ctl00_mainContentPlaceHolder_PendingContactUC1_SearchButton'
PERSON_IN_CUSTODY_INFORMATION_DIV_ID = 'ctl00_mainContentPlaceHolder_PendingContactUC1_inmatesGridViewPanel'
INVITATION_ACCEPT_BUTTON_ID = 'ctl00_mainContentPlaceHolder_PendingContactUC1_addInmateButton'
RECORD_NOT_FOUND_SPAN_ID = 'ctl00_mainContentPlaceHolder_PendingContactUC1_ResultLabel'
HEADERS_FOR_ACCEPT_INVITE = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.corrlinks.com/PendingContact.aspx',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Requested-With': 'XMLHttpRequest',
    'X-MicrosoftAjax': 'Delta=true'
}
