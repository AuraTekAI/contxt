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

"""
This lua script handles the process of sending a reply through a web form using the Splash browser.

Parameters:
- splash (Splash): The Splash browser instance for rendering and interacting with web pages
- args (table): A table containing the following keys:
    - splash_cookies (table): A list of cookies to be initialized in the Splash browser
    - headers (table): A table containing HTTP headers, including 'User-Agent', 'Referer', and 'Cookie'
    - reply_url (string): The URL of the reply page to be loaded in the Splash browser
    - message_content (string): The content of the reply message to be entered into the text box

Returns:
- table: A table containing the following keys:
    - html (string): The HTML content of the page after form submission
    - message (string): A message indicating the result of the form submission process
    - element_found (bool): True if the confirmation element was found, indicating a successful submission; False otherwise
    - text_box_message (string): A message indicating whether the text box was found and interacted with successfully

This script initializes the Splash browser with cookies and custom headers,
navigates to the specified reply URL, and checks for the presence of the text box.
It then enters the reply message, submits the form, and waits for the confirmation element
to appear, indicating a successful form submission. The process includes handling
redirects and ensuring the correct headers and cookies are used throughout.
"""
LUA_SCRIPT = '''
    function main(splash, args)

        -- below line is setting the cookies in the splash browser window.
        -- these cookies were sent with the post request.
        -- cookies are required because in case of any redirects,
        -- without cookies we are redirected to the login page.
        splash:init_cookies(args.splash_cookies)

        -- below line sets the private mode off.
        -- by default all splash windows are opened in private mode.
        splash.private_mode_enabled = false

        -- below lines are setting the headers inside the splash browser window.
        splash:set_custom_headers({
            ["User-Agent"] = args.headers["User-Agent"],
            ["Referer"] = args.headers["Referer"],
            ["Cookie"] = args.cookies
        })

        -- below lines are opening the sent reply_url in the post request
        -- in the splash browser window
        splash:go(args.reply_url)
        splash:wait(1.5)

        -- below is javascript function that checks the textbox availability on the web page.
        -- this is the same textbox in which the reply message will be entered.
        local check_element_existence_text_box = splash:jsfunc([[
            function() {
                var element = document.getElementById('ctl00_mainContentPlaceHolder_messageTextBox');
                return element !== null;
            }
        ]])

        -- below lines are running the above function.
        -- if the textbox is found on the web page, then proceed.
        -- if not found then return the response.
        -- because no point in continuing.
        local element_found_text_box = false
        local text_box_message = ""
        if check_element_existence_text_box() then
            element_found_text_box = true
            text_box_message = text_box_message .. "Text box found"
        else
            return {
                html = splash:html(),
                message = "Text box not found",
                element_found = element_found_text_box,
                text_box_message = "Text box not found"
            }
        end

        -- below function convert the latest cookies to a string format,
        -- because in request headers the cookies are accepted in a string format.
        local function format_cookies(cookies)
            local cookie_parts = {}
            for _, cookie in ipairs(cookies) do
                table.insert(cookie_parts, cookie.name .. "=" .. cookie.value)
            end
            return table.concat(cookie_parts, "; ")
        end

        -- below lines get the latest cookies from the splash browser window
        -- and send them to the above function for conversion.
        -- the cookies returned by the function are stored in the headers,
        -- to be used in further requests.
        local initial_cookies = splash:get_cookies()
        local initial_cookie_header = format_cookies(initial_cookies)
        splash:set_custom_headers({
            ["User-Agent"] = args.headers["User-Agent"],
            ["Referer"] = args.headers["Referer"],
            ["Cookie"] = initial_cookie_header
        })

        -- below function finds the textbox and triggers its focus property,
        -- enters the message in the textbox.
        -- this message was sent in the post request.
        local enter_message_textbox = splash:jsfunc([[
            function(content) {
                var textBox = document.getElementById('ctl00_mainContentPlaceHolder_messageTextBox');
                if (textBox) {
                    textBox.focus();  // Focus on the textarea to simulate user interaction
                    textBox.value = content;  // Clear existing content
                    
                } else {
                    return 'Message text box not found';
                }
            }
        ]])
        -- below line calls the above function
        enter_message_textbox(args.message_content)


        -- below line maximizes the splash browser window
        splash:set_viewport_full()

        -- below function finds the send button using its id.
        -- then send a click event to the button.
        -- this ensures that the form submission is triggered properly.
        local submit_form = splash:jsfunc([[
            function() {
                var submitButton = document.getElementById('ctl00_mainContentPlaceHolder_sendMessageButton');
                if (submitButton) {
                    submitButton.dispatchEvent(new Event('click'));
                    return "Submit button clicked";
                } else {
                    console.error('Submit button not found');
                    return "Submit button not found";
                }
            }
        ]])

        -- below line is very important
        -- after a request, referer header in splash window is reset
        -- setting it again here to avoid errors.
        -- and then call the above function.
        splash:set_custom_headers({
            ["Referer"] = args.headers["Referer"]
        })
        local result_message = submit_form()
        
        -- this function checks for an element that has a message
        -- this is shown after the successful submission of the form
        local check_element_existence = splash:jsfunc([[
            function() {
                var element = document.getElementById('ctl00_mainContentPlaceHolder_messageLabel');
                return element !== null;
            }
        ]])

        -- below line do a few things:
        -- 1 set a timeout value and intialize a time value for tracking the time spent
        -- 2 calls the above function in a while loop which breaks on two conditions:
        -- max_wait_time is reached or the element is found.
        -- if the element is found, then set the element_found to true
        -- which indicates that the form was submitted successfuly.
        -- if after max_wait_time, the element was still not found, element_found remains false.
        -- indicating that some error occured during form submission.
        -- sets a message to guage the time spent in the whole process using wait_time. 
        local max_wait_time = 6
        local wait_time = 0
        while not check_element_existence() do
            if wait_time >= max_wait_time then
                break
            end
            splash:wait(0.5)
            wait_time = wait_time + 0.5
        end
        local element_found = false
        if check_element_existence() then
            element_found = true
            result_message = result_message .. " . Element found after " .. wait_time .. " seconds"
        end

        return {
            html = splash:html(),
            message = result_message,
            element_found = element_found,
            text_box_message = text_box_message
        }
    end
'''