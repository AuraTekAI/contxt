
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
    '3736625367' : [],
    '3736550349' : [],
}

"""
PROCESSED DATA CONSTANTS
"""
PROCESSED_DATA_STATUS_CHOICES = [('processed', 'Processed'), ('pending', 'Pending')]
