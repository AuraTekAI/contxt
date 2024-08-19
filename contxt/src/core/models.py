
from accounts.models import User
from utils.constants import *

from django.db import models

class UserMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message_content = models.TextField()
    message_type = models.CharField(max_length=30)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f'Message for {self.user.name}'

    class Meta:
        db_table = 'user_messages'
        verbose_name = 'user_messages'
        verbose_name_plural = 'user_messages'
        indexes = [
            models.Index(fields=['user']),
        ]


class Email(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message_id = models.CharField(max_length=100, unique=True)
    sent_date_time = models.DateTimeField()
    subject = models.CharField(max_length=100)
    body = models.TextField()
    is_processed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return self.subject

    class Meta:
        db_table = 'emails'
        verbose_name = 'emails'
        verbose_name_plural = 'emails'
        indexes = [
            models.Index(fields=['user', 'sent_date_time']),
            models.Index(fields=['is_processed']),
        ]


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contact_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return self.contact_name

    class Meta:
        db_table = 'contacts'
        verbose_name = 'contacts'
        verbose_name_plural = 'contacts'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['phone_number']),
        ]


class SMS(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    message = models.TextField()
    text_id = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    direction = models.CharField(max_length=10, choices=SMS_DIRECTION_CHOICES)
    status = models.CharField(max_length=10, choices=SMS_STATUS_CHOICES)
    is_processed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return self.text_id

    class Meta:
        db_table = 'sms'
        verbose_name = 'sms'
        verbose_name_plural = 'sms'
        indexes = [
            models.Index(fields=['contact']),
            models.Index(fields=['email']),
            models.Index(fields=['text_id']),
            models.Index(fields=['is_processed']),
        ]


class Log(models.Model):
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

    def _str_(self):
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

    def _str_(self):
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