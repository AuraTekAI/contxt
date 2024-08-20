
from accounts.models import User

from django.db import models

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
