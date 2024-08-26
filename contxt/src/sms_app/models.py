
from core.models import Contact
from process_emails.models import Email

from contxt.utils.constants import SMS_DIRECTION_CHOICES, SMS_STATUS_CHOICES

from django.db import models

class SMS(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    message = models.TextField()
    text_id = models.CharField(max_length=255, null=True, blank=True)
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
