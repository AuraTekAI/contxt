
from accounts.models import User, BotAccount

from django.db import models

class Email(models.Model):
    """
    Represents an email message associated with a user and processed by a bot.

    Attributes:
        user (ForeignKey): The user to whom the email belongs.
        bot (ForeignKey): The bot that retrieved or processed the email.
        message_id (CharField): A unique identifier for the email message.
        sent_date_time (DateTimeField): The date and time when the email was sent.
        subject (CharField): The subject line of the email.
        body (TextField): The body content of the email.
        is_processed (BooleanField): Flag indicating whether the email has been processed.
        updated_at (DateTimeField): The timestamp when the email record was last updated.
        created_at (DateTimeField): The timestamp when the email record was created.

    Methods:
        __str__():
            Returns a string representation of the email, which is the subject of the email.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bot = models.ForeignKey(BotAccount, on_delete=models.CASCADE, null=True, blank=True)

    message_id = models.CharField(max_length=100, blank=True, null=True)
    subject = models.CharField(max_length=100)
    body = models.TextField()

    is_processed = models.BooleanField(default=False)

    sent_date_time = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Returns the string representation of the email.

        This is the subject of the email.

        Returns:
            str: The subject of the email.
        """
        return self.subject

    class Meta:
        db_table = 'emails'
        verbose_name = 'emails'
        verbose_name_plural = 'emails'
        indexes = [
            models.Index(fields=['user', 'sent_date_time']),
            models.Index(fields=['is_processed']),
            models.Index(fields=['bot']),
        ]
