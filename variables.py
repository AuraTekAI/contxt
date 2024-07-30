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
    "DB_IP": DB_IP,
    "DB_USERNAME": DB_USERNAME,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_NAME": DB_NAME,
    "CONN_STR": f"DRIVER={{SQL Server}};SERVER={DB_IP};DATABASE={DB_NAME};UID={DB_USERNAME};PWD={DB_PASSWORD}"
}

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
EMAIL1_USERNAME = "bradleyaroth@gmail.com"
EMAIL1_PASSWORD = "knxq vmyu eigo tawz"
EMAIL2_USERNAME = "XYZCorrlink@gmail.com"
EMAIL2_PASSWORD = "123456PasswordPleaseChangeThis"
EMAIL3_USERNAME = "XYZCorrlink@gmail.com"
EMAIL3_PASSWORD = "123456PasswordPleaseChangeThis"
EMAIL4_USERNAME = "XYZCorrlink@gmail.com"
EMAIL4_PASSWORD = "123456PasswordPleaseChangeThis"
EMAIL5_USERNAME = "XYZCorrlink@gmail.com"
EMAIL5_PASSWORD = "123456PasswordPleaseChangeThis"