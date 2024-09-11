
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
    'INVALID_PHONE_NUMBER': {
        'type': 'error',
        'content': "Invalid phone number format. Please provide a 10-digit valid phone number."
    },
    'INVALID_EMAIL': {
        'type': 'error',
        'content': "Invalid email address format. Please provide a valid email address."
    },
    'CONTACT_NAME_REQUIRED': {
        'type': 'error',
        'content': "Contact name is required. Please provide a name for the contact."
    },
    'CONTACT_NOT_FOUND': {
        'type': 'error',
        'content': "Contact {detail} not found."
    },
    'CONTACT_ALREADY_EXISTS': {
        'type': 'info',
        'content': "Contact {detail} already exists."
    },
    'CONTACT_ADDED_SUCCESSFULLY': {
        'type': 'success',
        'content': "Contact {detail} added successfully."
    },
    'CONTACT_UPDATED_SUCCESSFULLY': {
        'type': 'success',
        'content': "Contact {detail} updated successfully."
    },
    'CONTACT_REMOVED_SUCCESSFULLY': {
        'type': 'success',
        'content': "Contact {detail} removed successfully."
    },
    'UNKNOWN_COMMAND': {
        'type': 'error',
        'content': "Unknown command. Please provide a valid action (Add, Update, Remove, Contact List)."
    },
    'CONTACT_LIST': {
        'type': 'info',
        'content': 'Below is your current contact list: \n {all_contacts}'
    },
    'EMAIL_REQUIRED_FOR_ADD': {
        'type': 'error',
        'content': 'Email is required for adding a new email.'
    },
    'EMAIL_REQUIRED_FOR_UPDATE': {
        'type': 'error',
        'content': 'Email is required for updating email.'
    }
}
