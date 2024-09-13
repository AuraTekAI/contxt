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
    splash:go(args.reply_url)
    splash:wait(1.5)

    -- Click the element in the address box
    splash:runjs([[
        document.getElementById('ctl00_mainContentPlaceHolder_addressBox_addressTextBox').click();
    ]])
    splash:wait(1.5)

    -- JavaScript to find and click the checkbox matching pic_number
    local pic_number = args.pic_number
    local result = splash:evaljs([[
        var pic_number = ']] .. pic_number .. [[';
        var rows = document.querySelectorAll('#ctl00_mainContentPlaceHolder_addressBox_addressGrid tr');
        var found = null;
        for (var i = 1; i < rows.length; i++) {
            var addressCell = rows[i].cells[1];
            if (addressCell && addressCell.textContent.includes(pic_number)) {
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

    -- Input the subject "Welcome to ConTXT" in the subject text box
    splash:runjs([[
        document.getElementById('ctl00_mainContentPlaceHolder_subjectTextBox').value = 'Subject: Welcome to ConTXT';
    ]])

    -- Input the message in the message text area
    splash:runjs([[
        document.getElementById('ctl00_mainContentPlaceHolder_messageTextBox').value = 'A welcome message sent to you by ConTXT team. Thank you for choosing our services.';
    ]])

    -- Call the sendMessage function directly
    splash:runjs([[
        sendMessage(new Event('click'));
    ]])

    -- Allow time for postback or processing
    splash:wait(2.5)

    -- Return HTML, screenshot, and found row content
    return {
        html = splash:html(),
        screenshot = splash:png(),
        found_row = result,
        cookies = splash:get_cookies() -- Return cookies for subsequent requests
    }
end
