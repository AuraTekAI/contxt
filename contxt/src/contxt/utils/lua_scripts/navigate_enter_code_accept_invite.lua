-- Automates the process of navigating to a webpage, entering an invitation code, and accepting an invitation.

-- Parameters:
-- - splash (Splash): The Splash instance used for rendering and interacting with the webpage.
-- - args (table): A table containing configuration and data for the process. It includes:
--     - splash_cookies (table): Cookies to initialize in the Splash browser session.
--     - headers (table): Custom HTTP headers to set for the requests. Includes 'User-Agent' and 'Referer'.
--     - cookies (string): A string of cookies formatted for the 'Cookie' HTTP header.
--     - url (string): The URL to navigate to.
--     - invite_code_box_id (string): The HTML id of the textbox where the invitation code will be entered.
--     - invitation_code (string): The invitation code to input into the textbox.
--     - invitation_code_go_button_id (string): The HTML id of the button to submit the invitation code.
--     - person_in_custody_information_div_id (string): The HTML id of the div containing the person in custody information.
--     - invitation_accept_button_id (string): The HTML id of the button to accept the invitation.
--     - record_not_found_span_id (string): The HTML id of the span indicating that the record was not found.

-- Returns:
-- - table: A table containing the results of the operation with the following keys:
--     - html (string): The HTML content of the current page.
--     - element_found (boolean): Whether the required HTML elements were found during the process.
--     - is_processed (boolean): Indicates if the invitation was successfully processed.
--     - message (string): A message describing the result of each step in the process.
--     - extra_messages (string): Additional messages about intermediate steps or findings.
--     - error_message (string): Any error message encountered during the process.

-- Process Overview:
-- 1. **Initialize Cookies**:
--     - Set the cookies in the Splash browser session as per `args.splash_cookies`.

-- 2. **Disable Private Mode**:
--     - Ensure that private mode is turned off to retain cookies.

-- 3. **Set Custom Headers**:
--     - Configure custom headers (`User-Agent`, `Referer`, and `Cookie`) for the HTTP requests.

-- 4. **Navigate to URL**:
--     - Go to the specified URL and wait for the page to load.

-- 5. **Check for Invitation Code Textbox**:
--     - Use JavaScript to check if the invitation code textbox exists on the page.
--     - If not found, return an error message.

-- 6. **Enter Invitation Code**:
--     - Input the invitation code into the textbox using JavaScript.
--     - Log the result of the operation.

-- 7. **Submit the Invitation Code**:
--     - Find and click the "Go" button to submit the invitation code.
--     - Verify the presence of the button and log any issues encountered.

-- 8. **Check for Record Not Found**:
--     - Verify if a span indicating "Record not found" is present.
--     - If found, return an appropriate error message.

-- 9. **Check for Person in Custody Information**:
--     - Check if the div containing information about the person in custody exists.
--     - Log any issues if the div is not found.

-- 10. **Accept the Invitation**:
--     - Find and click the "Accept" button to finalize the invitation process.
--     - Log the results and wait for the page to update.

-- 11. **Return Results**:
--     - Return a table containing the HTML of the page, status of the element checks, process status and messages.

function main(splash, args)
    -- Set the cookies in the splash browser window
    splash:init_cookies(args.splash_cookies)

    -- Disable private mode
    splash.private_mode_enabled = false

    -- Set custom headers
    splash:set_custom_headers({
        ["User-Agent"] = args.headers["User-Agent"],
        ["Referer"] = args.headers["Referer"],
        ["Cookie"] = args.cookies
    })

    -- Open the URL
    splash:go(args.url)
    splash:wait(2.5)

    -- variables to keeps track of invitation code success or failure
    local is_processed = false
    local records_not_found_span_id = args.record_not_found_span_id

    local invite_box_id = args.invite_code_box_id

    -- JavaScript function to check the invitation code textbox existence
    local check_element_existence = splash:jsfunc([[
        function(id) {
            var element = document.getElementById(id);
            return element !== null;
        }
    ]])

    -- Run the above function and pass the invite_box_id
    local element_found_text_box = check_element_existence(invite_box_id)
    local extra_messages = ""

    -- If the textbox is found, update the messages
    if element_found_text_box then
        extra_messages = "Invitation code textbox found"
    else
        return {
            html = splash:html(),
            element_found = element_found_text_box,
            is_processed = is_processed,
            message = "",
            extra_messages = extra_messages,
            error_message = "Invitation code textbox not found",
            screenshot = splash:png()
        }
    end

    -- JavaScript function to enter the invitation code in the textbox
    local enter_invitation_code_textbox = splash:jsfunc([[
        function(invitation_code, invite_box_id) {
            var textBox = document.getElementById(invite_box_id);
            if (textBox) {
                textBox.focus();  // Focus on the textarea to simulate user interaction
                textBox.value = invitation_code;  // Enter the content in the textbox
                return 'Invitation code entered successfully';
            } else {
                return 'Invitation code textbox not found';
            }
        }
    ]])
    -- Call the above function to enter the invitation code
    local message = enter_invitation_code_textbox(args.invitation_code, invite_box_id)


    -- JavaScript function to find a button using its ID and simulate a click event.
    local submit_form = splash:jsfunc([[
        function(id) {
            var button = document.getElementById(id);
            if (button) {
                button.click();
                return id +  " button clicked";
            } else {
                return id + " button not found";
            }
        }
    ]])

    -- Re-set the Referer header in Splash to avoid potential errors after the request.
    splash:set_custom_headers({
        ["Referer"] = args.headers["Referer"]
    })

    -- Check if the "Go" button exists and update the messages.
    local invitation_code_go_button_id = args.invitation_code_go_button_id
    local element_found_go_button = check_element_existence(invitation_code_go_button_id)
    if element_found_go_button then
        extra_messages = extra_messages .. ". " .. "Go button found"
    else
        return {
            html = splash:html(),
            element_found = element_found_go_button,
            is_processed = is_processed,
            message = "",
            extra_messages = extra_messages,
            error_message = "Go button not found",
            screenshot = splash:png()
        }
    end
    splash:init_cookies(args.splash_cookies)
    -- Click the "Go" button and wait for the page to update.
    local result_message = submit_form(invitation_code_go_button_id)
    splash:wait(1.5)
    message = message .. ". " .. result_message


    -- Check if the "Record not found" span is present.
    local element_found_span = check_element_existence(records_not_found_span_id)
    if element_found_span then
        return {
            html = splash:html(),
            element_found = not(element_found_span),
            is_processed = true,
            message = message,
            extra_messages = extra_messages,
            error_message = "Record not found. Which either means the code has already been used or it doesn't exist.",
            screenshot = splash:png()
        }
    end



    -- Check if the person in custody information div exists.
    local person_in_custody_div_id = args.person_in_custody_information_div_id
    local element_found_div = check_element_existence(person_in_custody_div_id)
    if element_found_div then
        extra_messages = extra_messages .. ". " .. "Person in custody information div found"
    else
        return {
            html = splash:html(),
            element_found = element_found_div,
            is_processed = is_processed,
            message = message,
            extra_messages = extra_messages,
            error_message = "Person in custody information div not found",
            screeshot = splash:png()
        }
    end

    -- Check if the accept button exists.
    local accept_button_id = args.invitation_accept_button_id
    local element_found_accept_button = check_element_existence(accept_button_id)
    if element_found_accept_button then
        extra_messages = extra_messages .. ". " .. "Accept button found"
    else
        return {
            html = splash:html(),
            element_found = element_found_accept_button,
            is_processed = is_processed,
            message = message,
            extra_messages = extra_messages,
            error_message = "Accept button not found",
            screenshot = splash:png()
        }
    end

    splash:init_cookies(args.splash_cookies)
    splash:set_custom_headers({
        ["Referer"] = args.headers["Referer"]
    })

    -- Click the accept button and wait for the page to update.
    local result_message = submit_form(accept_button_id)
    splash:wait(3)

    message = message .. ". " .. result_message

    -- Return the final result with HTML content, element check status, process status, and messages.
    return {
        html = splash:html(),
        element_found = element_found_text_box,
        is_processed = true,
        message = message,
        extra_messages = extra_messages,
        error_message = "",
        screenshot = splash:png()
    }
end
