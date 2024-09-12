
# IMPORTANT: if you have to make changes in these constant values, then please make sure that their position doesn't change.

"""
SMS MODEL CONSTANTS
"""
SMS_DIRECTION_CHOICES = [('Inbound', 'Inbound'), ('Outbound', 'Outbound')]
SMS_STATUS_CHOICES = [('Sent', 'Sent'), ('Delivered', 'Delivered'), ('Failed', 'Failed'), ('Unknown', 'Unknown')]

"""
LOG MODEL CONSTANTS
"""
LOG_LEVEL_CHOICES = [('DEBUG', 'DEBUG'), ('INFO', 'INFO'), ('WARNING', 'WARNING'), ('ERROR', 'ERROR'), ('CRITICAL', 'CRITICAL')]

"""
TRANSACTION MODEL CONSTANTS
"""
TRANSACTION_TYPE_CHOICES = [('Credit', 'Credit'), ('Debit', 'Debit')]
TRANSACTION_STATUS_CHOICES = [('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed')]

"""
SMS TABLE SEED DATA
"""
SMS_TABLE_SEED_DATA = {
    '3736625367' : [] # TODO: Add some random message id from every bot below
}

"""
PROCESSED DATA CONSTANTS
"""
PROCESSED_DATA_STATUS_CHOICES = [('processed', 'Processed'), ('pending', 'Pending')]

"""
CURRENT TASKS RUN BY BOTS
"""
# Keep adding the names of modules here to dynamically add logger configurations.
CURRENT_TASKS_RUN_BY_BOTS = {
    'send_sms' : 'send_sms',
    'push_emails' : 'push_emails',
    'pull_emails' : 'pull_emails',
    'accept_invites' : 'accept_invites',
    'receive_sms' : 'receive_sms',
    'contact_management' : 'contact_management',
    'send_contact_management_responses' : 'send_contact_management_responses'
}


"""
CONTACT MANAGEMENT RESPONSE CONSTANTS
"""
CONTACT_MANAGEMENT_RESPONSE_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('sent', 'Sent'),
    ('failed', 'Failed'),
]

MESSAGES = {
    'WELCOME_STATUS': {
        'type': 'info',
        'content': """Subject line: Welcome to ConTXT! Your Messaging Status and Guide

        ------------------------------------------------------------------------------------------------------------------------------
        MESSAGE STATUS FOR EXISTING USERS

        Here is the status of your last 20 messages:
        DATE      TIME       CONTACT        MESSAGE ID      DELIVERED

        You have ## of 500 messages remaining for the month. Your 500 messages refresh on DATE.

        ------------------------------------------------------------------------------------------------------------------------------
        CURRENT CONTXT ACCOUNTS TO FRIEND

        Friend the following accounts to start messaging:
        {bot_accounts}

        ------------------------------------------------------------------------------------------------------------------------------
        GET STARTED GUIDE

        Thank you for choosing ConTXT as your inmate messaging service provider! Here are some basic instructions to get you started and connected to your cherished loved ones.

        Quick reference on subject line formatting for key ConTXT functions:
        Add Contact Number
        Add Contact Email
        Update Contact Number
        Update Contact Email
        Remove Contact
        Contact List
        Text [CONTACT]
        Set ScreenName
        Private
        Public
        PenPal [SCREENNAME]

        ------------------------------------------------------------------------------------------------------------------------------
        How to Send a Text to a Number:

        You may send an SMS message directly by placing the recipient's number, area code included, into the subject line of a newly composed CORRLINKS message.

        Example:
        Subject: Text 5559996666
        Hi Person, I enjoyed our visit last week.

        Note: The system will recognize 10 numbers formatted in any way as a phone number (with or without dashes).

        ------------------------------------------------------------------------------------------------------------------------------
        How to Add or Update a Contact:

        1. Compose a new CORRLINKS message to one of your ConTXT friend accounts.
        2. Place "Add Contact" in the subject line.
        3. Include the contact's name followed by the email address or phone number in the body of the email.

        Example for adding:
        Subject: Add Contact Number {Name_Of_The_Contact} {Phone_Number}
        OR
        Subject: Add Contact Number {Name_Of_The_Contact} {Email}

        ------------------------------------------------------------------------------------------------------------------------------
        How to Review Your Contact List:

        To review your contact list, please compose a new CORRLINKS message with "Contact List" in the subject line.

        ------------------------------------------------------------------------------------------------------------------------------
        How to Remove a Contact:

        To remove a contact from your list, compose a new CORRLINKS message with "Remove Contact" in the subject line.

        Example:
        Subject: Remove Contact {Name}

        ------------------------------------------------------------------------------------------------------------------------------
        If you need assistance, contact support at info@contxts.net with the subject line “Support”."""
    },

    'SIGNUP_INSTRUCTIONS': {
        'type': 'info',
        'content': """Subject: Subscription Needed to Activate Your ConTXT Account

        Dear {first_name},

        Thank you for reaching out to ConTXT. It appears that your account is not yet activated. To begin using our service, a family member or loved one needs to subscribe on your behalf.

        Next Steps:
        1. **Contact Your Family Member**: Ask them to visit our website at contxts.net to purchase a subscription.
        2. **Subscription Details**: Each $10 subscription buys 500 messages.
        3. **Activation**: Once the subscription is completed, you will receive an email confirming activation.

        If you have any questions, contact support at info@contxts.net with the subject line “Support”.

        Best regards,
        The ConTXT Team"""
    },

    'INSTRUCTIONAL_ERROR': {
        'type': 'error',
        'content': """Subject: Thank you for choosing ConTXT! Your Messaging Status and Guide
Dear {first_name},
We did not understand your recent request. Please refer to the following instructions for how to use the ConTXT service.


------------------------------------------------------------------------------------------------------------------------------
MESSAGE STATUS FOR EXISTING USERS

Here is the status of your last 20 messages:
DATE	TIME	CONTACT	MESSAGE ID	DELIVERED
{previous_text_messages_status}

You have  of 500 messages remaining for the month. Your 500 messages refresh on DATE.


------------------------------------------------------------------------------------------------------------------------------
CURRENT CONTXT ACCOUNTS TO FRIEND

Friend the following accounts to start messaging:
{bot_accounts}

------------------------------------------------------------------------------------------------------------------------------
GET STARTED GUIDE

Thank you for choosing ConTXT as your inmate messaging service provider! Here are
some basic instructions to get you started and connected to your cherished loved ones.

Quick reference on subject line formatting for key ConTXT functions:
Add Contact Number
Add Contact Email
Update Contact Number
Update Contact Email
Remove Contact
Contact List
Text [CONTACT]
Set ScreenName
Private
Public
PenPal [SCREENNAME]


------------------------------------------------------------------------------------------------------------------------------
How Send a Text to a Number

You may an SMS message directly to your loved one by simply placing their number, area code included, into the subject line of a newly composed CORRLINKS message.

Example:
Subject: Text 5559996666
Hi Bugs, I enjoyed our visit last week.

Note: The system will recognize 10 numbers formatted in any way as a phone number, so you can add dashes, periods, spaces, or no spaces in the number, whatever you prefer.
While this method will work, we highly suggest for both convenience and privacy that you first build your contact list.

------------------------------------------------------------------------------------------------------------------------------
How to Add or Update a Contact

1. Compose a new CORRLINKS message to one of your ConTXT friend accounts.
2. Place "Add Contact" in the subject line.
3. Include the contact's name followed by the email address or phone number in the body of the email.
- Contact names are not case-sensitive, so you can use all caps, no caps, or some caps.
- You can add multiple contacts in one “Add Contact” message.
- To send a message to your contact, you will need to type out the name exactly as you did when you set up the contact, so consider leaving off last names or using an initial at the end if you have two contacts named Daffy, for example.
- The system will recognize 10 numbers formatted in any way as a phone number, so you can add dashes, periods, spaces, or no spaces in the number, whatever you prefer.
- The system will recognize a group of text with the @ symbol as an email address. Please note the system does not yet send emails, but you can add email addresses to your contact list anyway if you choose to do so.
Example:
Subject: Add Contact Number BugsB 5555555555
Example:
Subject: Add Contact Email BugsB bugs@carrots.com

How to Update an Existing Contact

Compose a new CORRLINKS message to one of your ConTXT friend accounts.
Type “Update Contact” in the subject line.
Include the contact's name followed by the new email address or phone number in the body of the email.

Example:
Subject: Update Contact Email YosemiteSam sam@newwildwest.com

Example:
Subject: Update Contact Number YosemiteSam 5555555555

When the contact has been added or updated, you will receive a confirmation email from ConTXT Support
informing you that your contact list has been updated along with a receipt of your complete
contact list.

------------------------------------------------------------------------------------------------------------------------------
How to Review Your Contact List

To review your contact list, please do the following:
1. Compose a new CORRLINKS message to one of your ConTXT friend accounts.
2. Type "Contact List" into the subject line.
3. Click 'Send' in the top left corner of your screen.

------------------------------------------------------------------------------------------------------------------------------
How to Remove a Contact

To remove a contact from your list, please do the following:
1. Compose a new CORRLINKS message to one of your ConTXT friend accounts.
2. Type "Remove Contact" in the subject line.
3. Type the name of the contact you wish to remove in the body.
4. Click 'Send' in the top left corner of your screen.

Example:
Subject: Remove Contact Daffy

------------------------------------------------------------------------------------------------------------------------------
How to Set Your ScreenName for PenPal

ConTXT also provides a unique "PenPal" service allowing users to message each other back and
forth across our platform. You may set up your screen name by doing the following:

1. Compose a new CORRLINKS message to one of your ConTXT friend accounts.
2. Type your desired screen name into the body of the message.

Example:
Subject: Set ScreenName
PorkyPig69 31 M

You will notice that after the screen name, there is the number '31' followed by the letter 'M'. This indicates that I am 31 years of age and male. When a user requests the PenPal list, all screen names will appear on the PenPal list along with name and sex.
If you wish to update your ScreenName or Details later, you can send the same type of message
Compose a new CORRLINKS message to one of your ConTXT friend accounts.
Type “Set ScreenName” in the subject line.
Include your new ScreenName and Details in the body of the message.
Your existing details will be updated with your new details.

Example:
Subject line: Set ScreenName
PorkyPig69 32 M

If you would like to set a screen name but would not like to appear on the PenPal list, here’s how:
1. Compose a new CORRLINKS message to one of your ConTXT friend accounts.
2. Type "Private" into the subject line.
3. Click 'Send' in the top left corner of your screen.

Example:
Subject: Private
(nothing in the body)

If you want to go Public on the PenPal list again, here’s how:
1. Compose a new CORRLINKS message to one of your ConTXT friend accounts.
2. Type "Public" into the subject line.
3. Click 'Send' in the top left corner of your screen.


------------------------------------------------------------------------------------------------------------------------------
How to Send a Message to Family or PenPal

1. Compose a new CORRLINKS message to one of your ConTXT friend accounts.
2. Type “Text [CONTACT]” or “PenPal [SCREENNAME]” into the subject line, replacing [CONTACT] or [SCREENNAME] with the family member or user you want to message.
3. Type your message into the body.
4. Click 'Send' in the top left corner of your screen.

Example 1:
Subject: Text Daffy
Miss you buddy. How’s Bugs doing?

Example 2:
Subject: PenPal PetuniaPig1999
Hi Petunia, nice screen name.

------------------------------------------------------------------------------------------------------------------------------
How to Get Help with Your Account
If you need any assistance, please contact our support team at info@contxts.net with the subject line “Support”.
"""
    },

    'FAMILY_CONTACT_UPDATE': {
        'type': 'info',
        'content': """Subject: Family Contact Update

Dear {first_name},

Thank you for using ConTXT to stay connected with your loved ones. Below is the summary of your recent contact update request.

New Contacts:
{new_contacts}

Existing Contacts:
{existing_contacts}

Failed Contacts:
{failed_contacts}

Instructions for Adding/Updating Contacts:

Compose a new CORRLINKS message to one of your ConTXT friend accounts.
{bot_accounts}

Place "Add Contact" in the subject line.

Include the contact's name followed by the email address or phone number in the body of the email.

Contact names are not case-sensitive, so you can use all caps, no caps, or some caps.

You can add multiple contacts in one “Add Contact” message.

To send a message to your contact, you will need to type out the name exactly as you did when you set up the contact, so consider leaving off last names or using an initial at the end if you have two contacts named Daffy, for example.

The system will recognize 10 numbers formatted in any way as a phone number, so you can add dashes, periods, spaces, or no spaces in the number, whatever you prefer.

The system will recognize a group of text with the @ symbol as an email address. Please note the system does not yet send emails, but you can add email addresses to your contact list anyway if you choose to do so.

Example:
Subject: Add Contact Number BugsB 5555555555
Example:
Subject: Add Contact Email BugsB bugs@carrots.com


Update an Existing Contact:

Compose a new CORRLINKS message to one of your ConTXT friend accounts.

Type “Update Contact” in the subject line.

Include the contact's name followed by the new email address or phone number in the body of the email.

Example:
Subject: Update Contact Email YosemiteSam sam@newwildwest.com

Example:
Subject: Update Contact Number YosemiteSam 5555555555

View Existing Contacts:

Compose a new CORRLINKS message to one of your ConTXT friend accounts.

Type "Contact List" in the subject line.

Example:

Subject: Contact List



You will receive a confirmation email with an updated list of your contacts once the changes have been processed.



If you need any assistance, please contact our support team at info@contxts.net with the subject line “Support”.



For assistance with adding/updating contacts, contact support at info@contxts.net.
Best regards,

The ConTXT Team"""
    },

    'MESSAGE_SENT_CONFIRMATION': {
        'type': 'success',
        'content': """Subject: Confirmation: Your Text Message Has Been Sent

        Dear {first_name},

        We are pleased to inform you that your text message has been successfully sent.

        Message Details:
        - Recipient Name: {recipient_name}
        - Recipient Phone Number: {recipient_phone}
        - Sent Date and Time: {sent_datetime}

        For assistance, contact support at info@contxts.net."""
    },


    'CONTACT_NOT_FOUND': {
        'type': 'error',
        'content': """Subject: Contact Not Found: Here Are Your Current Contacts

Dear {first_name},

We couldn't find the contact you were trying to reach. Below are your current contacts:

{existing_contacts}

To add a new contact, compose a new message with "Add Contact Number Name Phone" or "Add Contact Email Name Email" in the subject line.

For assistance, contact support at info@contxts.net."""
    },

    'CONTACT_LIST': {
        'type': 'info',
        'content': """Subject: Here Are Your Current Contacts

Dear {first_name},

Here is your current contact list:

{existing_contacts}

To add a new contact, compose a new message with "Add Contact Number Name Phone" or "Add Contact Email Name Email" in the subject line.

For assistance, contact support at info@contxts.net."""
    },

    'FAMILY_TEXT_TO_CL': {
        'type': 'info',
        'content': """Subject: New Message from {contact_name}

        Dear {first_name},

        You have received a new message from {contact_name}.

        Message Details:
        - Sender Name: {contact_name}
        - Sender Phone Number: {sender_phone_number}
        - Message Received At: {received_time}

        To reply, simply hit Reply, and your message will be sent as a text to {contact_name}."""
    },

    'TEXT_NOT_SENT_ERROR': {
        'type': 'error',
        'content': """Subject: Error: Your Text Message Could Not Be Sent

        Dear {first_name},

        We regret to inform you that your text message could not be sent.

        Message Details:
        - Recipient Name: {recipient_name}
        - Recipient Phone Number: {recipient_phone}
        - Attempted Sent Date and Time: {attempted_sent_datetime}

        Reason for Failure: {error_reason}

        Please try sending the message again. Contact support at info@contxts.net if you need assistance."""
    },

    'SCREENNAME_CONFIRMATION': {
        'type': 'success',
        'content': """Subject: Your ScreenName Has Been Accepted

        Dear {first_name},

        Congratulations! Your ScreenName has been successfully accepted.

        ScreenName: {screen_name}
        Your Details: {AGE} {SEX}

        For updates, compose a new message with "Set ScreenName" in the subject line."""
    },
    'SCREENNAME_ERROR': {
                    'type': 'error',
                    'content': """Subject: ScreenName Not Accepted

            Dear {first_name},

            We regret to inform you that your ScreenName submission was not accepted.

            Please choose a different ScreenName and resubmit."""
    },

    'LIST_PENPAL_USERS': {
            'type': 'info',
            'content': """Subject: Requested PenPal User List

            Dear {first_name},

            Thank you for your request! Below is the list of PenPal users:

            {penpal_list}

            To request a filtered list, specify your filter criteria in a new message with "Filter PenPal List" in the subject line."""
    }
}
