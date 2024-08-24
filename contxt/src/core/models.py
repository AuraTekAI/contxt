
from accounts.models import User
from contxt.utils.constants import *

from django.db import models

class UserMessage(models.Model):
    """
    Represents a message associated with a user.

    Attributes:
        user (ForeignKey): Reference to the User model.
        message_content (TextField): The content of the message.
        message_type (CharField): The type of the message (e.g., 'SMS', 'Email').
        updated_at (DateTimeField): Timestamp when the message was last updated.
        created_at (DateTimeField): Timestamp when the message was created.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message_content = models.TextField()
    message_type = models.CharField(max_length=30)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message for {self.user.name}'

    class Meta:
        db_table = 'user_messages'
        verbose_name = 'user_message'
        verbose_name_plural = 'user_messages'
        indexes = [
            models.Index(fields=['user']),
        ]


class Contact(models.Model):
    """
    Represents a contact associated with a user.

    Attributes:
        user (ForeignKey): Reference to the User model.
        contact_name (CharField): The name of the contact.
        phone_number (CharField): The phone number of the contact.
        email (EmailField): The email address of the contact, unique and optional.
        updated_at (DateTimeField): Timestamp when the contact was last updated.
        created_at (DateTimeField): Timestamp when the contact was created.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contact_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.contact_name

    class Meta:
        db_table = 'contacts'
        verbose_name = 'contacts'
        verbose_name_plural = 'contacts'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['phone_number']),
        ]


class Log(models.Model):
    """
    Represents a log entry for system or application events.

    Attributes:
        user (ForeignKey): Reference to the User model, optional.
        log_level (CharField): The level of the log (e.g., 'INFO', 'ERROR').
        module (CharField): The module or component that generated the log, optional.
        message (TextField): The content of the log message, optional.
        message_id (CharField): An identifier for the log message, optional.
        exception_details (TextField): Details of any exceptions encountered, optional.
        ip_address (CharField): The IP address associated with the log entry, optional.
        additional_data (TextField): Any additional data related to the log entry, optional.
        updated_at (DateTimeField): Timestamp when the log entry was last updated.
        created_at (DateTimeField): Timestamp when the log entry was created.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    log_level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES)
    module = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    message_id = models.CharField(max_length=255, null=True, blank=True)
    exception_details = models.TextField(null=True, blank=True)
    ip_address = models.CharField(max_length=50, null=True, blank=True)
    additional_data = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Log {self.id} - {self.log_level}'

    class Meta:
        db_table = 'logs'
        verbose_name = 'logs'
        verbose_name_plural = 'logs'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['log_level']),
        ]


class TransactionHistory(models.Model):
    """
    Represents a transaction history entry for a user.

    Attributes:
        user (ForeignKey): Reference to the User model.
        transaction_type (CharField): The type of the transaction (e.g., 'credit', 'debit').
        amount (DecimalField): The amount of the transaction.
        balance_before (DecimalField): The user's balance before the transaction.
        balance_after (DecimalField): The user's balance after the transaction.
        description (TextField): A description of the transaction, optional.
        status (CharField): The status of the transaction (e.g., 'completed', 'pending'), optional.
        reference_id (CharField): A reference identifier for the transaction, optional.
        updated_at (DateTimeField): Timestamp when the transaction was last updated.
        created_at (DateTimeField): Timestamp when the transaction was created.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    balance_before = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, null=True, blank=True)
    reference_id = models.CharField(max_length=60, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Transaction {self.id} - {self.transaction_type}'

    class Meta:
        db_table = 'transaction_history'
        verbose_name = 'transaction_history'
        verbose_name_plural = 'transaction_history'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['reference_id']),
            models.Index(fields=['status']),
        ]
