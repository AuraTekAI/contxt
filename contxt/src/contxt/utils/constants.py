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
    '3736435606' : [],
    '3736414498' : [],
    '3736366249' : [],
    '3735333329' : []

}
