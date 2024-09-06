-- This lua script handles the process of sending a reply through a web form using the Splash browser.

-- Parameters:
-- - splash (Splash): The Splash browser instance for rendering and interacting with web pages
-- - args (table): A table containing the following keys:
--     - splash_cookies (table): A list of cookies to be initialized in the Splash browser
--     - headers (table): A table containing HTTP headers, including 'User-Agent', 'Referer', and 'Cookie'
--     - reply_url (string): The URL of the reply page to be loaded in the Splash browser
--     - message_content (string): The content of the reply message to be entered into the text box

-- Returns:
-- - table: A table containing the following keys:
--     - html (string): The HTML content of the page after form submission
--     - message (string): A message indicating the result of the form submission process
--     - element_found (bool): True if the confirmation element was found, indicating a successful submission; False otherwise
--     - text_box_message (string): A message indicating whether the text box was found and interacted with successfully

-- This script initializes the Splash browser with cookies and custom headers,
-- navigates to the specified reply URL, and checks for the presence of the text box.
-- It then enters the reply message, submits the form, and waits for the confirmation element
-- to appear, indicating a successful form submission. The process includes handling
-- redirects and ensuring the correct headers and cookies are used throughout.

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
