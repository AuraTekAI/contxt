# Module Functions Documentation

## push_email.py

### 1. `capture_session_state(session)`
- **Description**: Captures the current state of the session, including headers and dynamic cookies.
- **Parameters**: 
  - `session` (requests.Session)
- **Returns**: dict containing the captured session state

### 2. `update_session_state(session, state)`
- **Description**: Updates the session with the captured state.
- **Parameters**:
  - `session` (requests.Session): The session object to update
  - `state` (dict): The state to apply to the session

### 3. `log_response_info(response)`
- **Description**: Logs detailed information about an HTTP response.
- **Parameters**: 
  - `response` (requests.Response)

### 4. `send_email_reply(session, form_data, message_content, message_id, session_state)`
- **Description**: Sends an email reply through the Corrlinks system.
- **Parameters**:
  - `session` (requests.Session)
  - `form_data` (dict): Form data extracted from the reply page
  - `message_content` (str): Content of the reply message
  - `message_id` (str): ID of the message being replied to
  - `session_state` (dict): Current state of the session
- **Returns**: bool indicating success or failure

### 5. `navigate_to_reply_page(session, message_id)`
- **Description**: Navigates to the reply page for a specific message.
- **Parameters**:
  - `session` (requests.Session)
  - `message_id` (str)
- **Returns**: tuple (response, form_data)

### 6. `extract_form_data(html)`
- **Description**: Extracts form data from an HTML page.
- **Parameters**: 
  - `html` (str)
- **Returns**: dict of form field names and values

### 7. `run_data_logger_push_email()`
- **Description**: Runs the data logger push email process.
- **Returns**: str indicating the result of the process

## db_ops.py

### 1. `set_email_callback(callback)`
- **Description**: Sets the email callback function.
- **Parameters**: 
  - `callback` (function)

### 2. `get_database_connection()`
- **Description**: Attempts to establish a database connection using the configuration.
- **Returns**: tuple (connection, cursor)

### 3. `check_connection(cursor)`
- **Description**: Tests the given database cursor by attempting to fetch a simple query.
- **Parameters**: 
  - `cursor` (pyodbc.Cursor)
- **Returns**: bool

### 4. `close_database_resources(db_connection, cursor)`
- **Description**: Properly closes the database resources.
- **Parameters**:
  - `db_connection` (pyodbc.Connection)
  - `cursor` (pyodbc.Cursor)

### 5. `save_emails(emails, connection, cursor)`
- **Description**: Saves a batch of emails to the database, including their message IDs.
- **Parameters**:
  - `emails` (list): List of dictionaries containing email data
  - `connection` (pyodbc.Connection)
  - `cursor` (pyodbc.Cursor)

### 6. `ensure_user_exists(connection, cursor, user_name_id)`
- **Description**: Ensures that a user exists in the database; adds the user if not present.
- **Parameters**:
  - `connection` (pyodbc.Connection)
  - `cursor` (pyodbc.Cursor)
  - `user_name_id` (str): String containing the user's name and ID
- **Returns**: str (user ID) or None

### 7. `save_contact_details(contact_name, phone, email, cursor)`
- **Description**: Saves the contact details into the Contacts table.
- **Parameters**:
  - `contact_name` (str)
  - `phone` (str, optional)
  - `email` (str, optional)
  - `cursor` (pyodbc.Cursor)

### 8. `check_user_active(full_name)`
- **Description**: Checks if a user is active in the database.
- **Parameters**: 
  - `full_name` (str)
- **Returns**: bool

### 9. `update_user_info(user_info)`
- **Description**: Updates user information in the database.
- **Parameters**: 
  - `user_info` (dict)

### 10. `log_sms_to_db(contact_id, message, status, text_id, number, direction)`
- **Description**: Logs an SMS message to the database.
- **Parameters**:
  - `contact_id` (int)
  - `message` (str)
  - `status` (str)
  - `text_id` (str)
  - `number` (str)
  - `direction` (str)

### 11. `update_sms_status_in_db(text_id, status)`
- **Description**: Updates the status of an SMS message in the database.
- **Parameters**:
  - `text_id` (str)
  - `status` (str)

### 12. `get_unprocessed_sms()`
- **Description**: Retrieves unprocessed SMS messages from the database.
- **Returns**: list of tuples

### 13. `update_sms_processed(text_id)`
- **Description**: Updates the processed status of an SMS message in the database.
- **Parameters**: 
  - `text_id` (str)

### 14. `get_user_info_by_contact_id(contact_id)`
- **Description**: Retrieves user information based on a contact ID.
- **Parameters**: 
  - `contact_id` (int)
- **Returns**: tuple or None

### 15. `get_contact_by_phone(db_connection, user_id, phone_number)`
- **Description**: Looks up a contact based on the phone number for a specific user.
- **Parameters**:
  - `db_connection`
  - `user_id` (int)
  - `phone_number` (str)
- **Returns**: dict or None

### 16. `parse_contact_emails(driver, db_connection, cursor)`
- **Description**: Fetches and parses contact emails to extract contact information.
- **Parameters**:
  - `driver`
  - `db_connection`
  - `cursor`

### 17. `parse_contact_info(email_body)`
- **Description**: Parses the email body to extract contact information using refined regex.
- **Parameters**: 
  - `email_body` (str)
- **Returns**: list of dicts

### 18. `insert_contacts_to_db(contacts, db_connection, user_id, driver, cursor)`
- **Description**: Inserts the contact information into the database after checking for duplicates.
- **Parameters**:
  - `contacts` (List[Dict])
  - `db_connection`
  - `user_id` (int)
  - `driver`
  - `cursor`

### 19. `send_contact_list_email(user_id, db_connection, cursor)`
- **Description**: Sends an email containing the user's current contact list.
- **Parameters**:
  - `user_id` (int)
  - `db_connection`
  - `cursor`

### 20. `remove_contact_from_db(contact_name, db_connection, user_id, cursor)`
- **Description**: Removes a contact from the database.
- **Parameters**:
  - `contact_name` (str)
  - `db_connection`
  - `user_id` (int)
  - `cursor`

### 21. `add_contact_email(email_body, db_connection, user_id, driver, cursor)`
- **Description**: Adds a contact email to the database.
- **Parameters**:
  - `email_body` (str)
  - `db_connection`
  - `user_id` (int)
  - `driver`
  - `cursor`

### 22. `add_contact_number(email_body, db_connection, user_id, driver, cursor)`
- **Description**: Adds a contact number to the database.
- **Parameters**:
  - `email_body` (str)
  - `db_connection`
  - `user_id` (int)
  - `driver`
  - `cursor`

### 23. `set_screen_name(body, db_connection, user_id, cursor)`
- **Description**: Sets the screen name for the user.
- **Parameters**:
  - `body` (str)
  - `db_connection`
  - `user_id` (int)
  - `cursor`

### 24. `set_private_mode(user_id, db_connection, cursor)`
- **Description**: Sets the user to private mode.
- **Parameters**:
  - `user_id` (int)
  - `db_connection`
  - `cursor`

## accept_invite.py

### 1. `log_request_info(url, method, headers, data=None, params=None, cookies=None)`
- **Description**: Logs detailed information about an HTTP request.
- **Parameters**:
  - `url` (str)
  - `method` (str)
  - `headers` (dict)
  - `data` (dict, optional)
  - `params` (dict, optional)
  - `cookies` (dict, optional)

### 2. `log_response_info(response)`
- **Description**: Logs detailed information about an HTTP response.
- **Parameters**: 
  - `response` (requests.Response)

### 3. `fetch_invite_code_and_name()`
- **Description**: Retrieves an invite code and associated name from emails.
- **Returns**: tuple (invite_code, email_id, full_name) or (None, None, None)

### 4. `extract_form_data(html)`
- **Description**: Extracts form data from an HTML page.
- **Parameters**: 
  - `html` (str)
- **Returns**: dict

### 5. `navigate_to_pending_contact(session)`
- **Description**: Navigates to the Pending Contact page on the Corrlinks website.
- **Parameters**: 
  - `session` (requests.Session)
- **Returns**: tuple (response, form_data) or (None, None)

### 6. `enter_invite_code(session, form_data, invite_code)`
- **Description**: Enters an invite code on the Pending Contact page.
- **Parameters**:
  - `session` (requests.Session)
  - `form_data` (dict)
  - `invite_code` (str)
- **Returns**: tuple (response, bool)

### 7. `accept_invitation(session, form_data, invite_code)`
- **Description**: Accepts an invitation on the Corrlinks website.
- **Parameters**:
  - `session` (requests.Session)
  - `form_data` (dict)
  - `invite_code` (str)
- **Returns**: bool

### 8. `process_invitation()`
- **Description**: Processes an invitation from start to finish.
- **Returns**: bool

### 9. `delete_invite_email(email_id)`
- **Description**: Deletes the invite email after successful processing.
- **Parameters**: 
  - `email_id` (str)

## pull_email.py

### 1. `process_unread_emails(session, db_connection, cursor)`
- **Description**: Processes unread emails from the Corrlinks inbox.
- **Parameters**:
  - `session` (requests.Session)
  - `db_connection`
  - `cursor`

### 2. `parse_ajax_response(response_text)`
- **Description**: Parses the AJAX response to extract the relevant HTML content.
- **Parameters**: 
  - `response_text` (str)
- **Returns**: str or None

### 3. `process_email_content(content, message_id)`
- **Description**: Processes the content of a single email.
- **Parameters**:
  - `content` (str)
  - `message_id` (str)
- **Returns**: dict

### 4. `extract_most_recent_message(full_message)`
- **Description**: Extracts the most recent message from a potentially threaded email conversation.
- **Parameters**: 
  - `full_message` (str)
- **Returns**: str

## send_sms.py

### 1. `send_sms_threaded(user_id=None, contact_id=None, to_number=None, message_body=None, message_id=None)`
- **Description**: Sends an SMS message using Textbelt's service in a separate thread.
- **Parameters**:
  - `user_id` (int, optional)
  - `contact_id` (int, optional)
  - `to_number` (str, optional)
  - `message_body` (str, optional)
  - `message_id` (str, optional)

### 2. `check_sms_status(text_id, user_id, message_id, message_body, to_number, contact_id, retry_count=0)`
- **Description**: Checks the delivery status of an SMS and updates the database.
- **Parameters**:
  - `text_id` (str)
  - `user_id` (int)
  - `message_id` (str)
  - `message_body` (str)
  - `to_number` (str)
  - `contact_id` (int)
  - `retry_count` (int, optional)

### 3. `send_failure_notification_email(user_id, to_number, contact_id)`
- **Description**: Sends a notification email to the user about SMS delivery failure.
- **Parameters**:
  - `user_id` (int)
  - `to_number` (str)
  - `contact_id` (int)

### 4. `process_sms_replies()`
- **Description**: Processes SMS replies received through the system.

### 5. `send_email_reply(contact_id, message, text_id, number)`
- **Description**: Sends an email reply for an incoming SMS message.
- **Parameters**:
  - `contact_id` (int)
  - `message` (str)
  - `text_id` (str)
  - `number` (str)

### 6. `check_quota(api_key)`
- **Description**: Checks the remaining SMS quota for the given API key.
- **Parameters**: 
  - `api_key` (str)
- **Returns**: int or None

### 7. `handle_long_email_reply(user_id, subject, body)`
- **Description**: Handles email replies that exceed the 13000 character limit.
- **Parameters**:
  - `user_id` (int)
  - `subject` (str)
  - `body` (str)

## login.py

### 1. `login_to_corrlinks()`
- **Description**: Logs into the Corrlinks website and returns a session object.
- **Returns**: requests.Session or None

This documentation provides an overview of the main functions in each module, their parameters, and return values. It can serve as a quick reference for understanding the structure and capabilities of the project.