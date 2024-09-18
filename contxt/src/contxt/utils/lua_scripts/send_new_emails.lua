-- Custom function to replace \n with \\n
local function escape_newlines(str)
    local result = ""
    for i = 1, #str do
        local char = str:sub(i, i)
        if char == "\n" then
            result = result .. "\\n"
        else
            result = result .. char
        end
    end
    return result
end

function main(splash, args)
    -- Initialize cookies from the initial request
    splash:init_cookies(args.splash_cookies)

    -- Disable private mode (ensures cookies are kept)
    splash.private_mode_enabled = false

    -- Set custom headers (User-Agent, Referer, etc.)
    splash:set_custom_headers({
        ["User-Agent"] = args.headers["User-Agent"],
        ["Referer"] = args.headers["Referer"]
    })

    -- Open the initial page
    splash:go(args.new_message_url)
    splash:wait(1.5)

    -- Click the element in the address box
    splash:runjs([[
        document.getElementById('ctl00_mainContentPlaceHolder_addressBox_addressTextBox').click();
    ]])
    splash:wait(1.5)

    -- Get the already transformed name in "Last First Middle" format
    local transformed_name = args.pic_name

    -- JavaScript to find and click the checkbox matching the transformed name
    local result = splash:evaljs([[
        var targetName = ']] .. transformed_name .. [[';
        var rows = document.querySelectorAll('#ctl00_mainContentPlaceHolder_addressBox_addressGrid tr');
        var found = null;

        for (var i = 1; i < rows.length; i++) {
            var addressCell = rows[i].cells[1];
            if (addressCell && addressCell.textContent.includes(targetName)) {
                found = addressCell.textContent;
                var checkbox = rows[i].querySelector('input[type="checkbox"]');
                if (checkbox) {
                    checkbox.click();
                }
                break;
            }
        }
        found;
    ]])
    splash:wait(1)
    splash:init_cookies(args.splash_cookies)

    splash:runjs([[
        document.getElementById('ctl00_mainContentPlaceHolder_addressBox_okButton').click();
    ]])

    -- Allow time for postback or processing
    splash:wait(2.5)

    -- Check message_to_send and handle string escaping manually
    local message_to_send = args.message

    -- Ensure message_to_send is a string and not nil
    if not message_to_send or type(message_to_send) ~= "string" then
        return {error = "message_to_send is nil or not a string", message_to_send = tostring(message_to_send)}
    end

    splash:runjs([[
        document.getElementById('ctl00_mainContentPlaceHolder_subjectTextBox').value = 'Subject: Welcome to ConTXT! Your Messaging Guide.';
    ]])

    -- Escape newlines manually using the custom function
    local escaped_message = escape_newlines(message_to_send)

    -- Insert the escaped message into the textarea
    splash:runjs([[
        var textarea = document.getElementById('ctl00_mainContentPlaceHolder_messageTextBox');
        textarea.value = ']] .. escaped_message .. [[';
    ]])

    splash:init_cookies(args.splash_cookies)
    -- Call the sendMessage function directly
    splash:runjs([[
        sendMessage(new Event('click'));
    ]])

    -- Allow time for postback or processing
    splash:wait(2.5)

    -- Return the final state and the escaped message for confirmation
    return {
        html = splash:html(),
        screenshot = splash:png(),
        found_row = result,
        final_url = splash:url(),
        escaped_message = escaped_message -- The message after manual escaping
    }
end



