from contxt.utils.constants import SMS_TABLE_SEED_DATA
from sms_app.models import SMS
from process_emails.models import Email
from accounts.models import User
from core.models import Contact

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.transaction import atomic
from django.contrib.auth.hashers import make_password
from django.utils import timezone

class Command(BaseCommand):
    """
    A Django management command to seed the database with initial data for testing purposes.

    This command creates a user and associated data if the user does not already exist.
    It also populates the database with example email and SMS data.
    """

    help = 'Seed DB with data to enable testing the implemented modules.'

    @atomic
    def handle(self, *args, **kwargs):
        """
        Executes the command to seed the database with data.

        This method:
        1. Creates a user with a specific `pic_number` if it does not already exist.
        2. Creates a contact for the user if no contact exists for this user.
        3. Seeds the database with example email and SMS data.

        The data for emails and SMS is obtained from `SMS_TABLE_SEED_DATA`.
        """

        # Create or get the user with a specific pic_number.
        user, created = User.objects.get_or_create(
            pic_number='15372010',
            defaults={
                'name': 'COOK ZACHARY',
                'is_active': False,
                'user_name': 'COOKZACHARY_15372010',
                'is_staff': False,
                'is_superuser': False,
                'password': make_password(settings.SUPER_SECRET_INITIAL_USER_PASSWORD)
            }
        )

        if created:
            # Notify that a new user was created.
            self.stdout.write(self.style.SUCCESS('Created user with pic_number 15372010.'))

            # Create a contact for the user if it does not already exist.
            if not Contact.objects.filter(user=user).exists():
                contact, contact_created = Contact.objects.get_or_create(
                    user=user,
                    defaults={
                        'contact_name': 'Bradley Roth',
                        'phone_number': f'+14024312303',
                        'email': f'{user.user_name}@example.com' if user.custom_email is None else user.custom_email,
                    }
                )

                if contact_created:
                    self.stdout.write(self.style.SUCCESS(f'Created contact for user {user.name}.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Contact for user {user.name} already exists.'))

            # Seed the database with example email and SMS data.
            for message_id in SMS_TABLE_SEED_DATA.keys():
                email = Email.objects.create(
                    user=user,
                    message_id=message_id,
                    sent_date_time=timezone.now(),
                    subject=f'Subject {message_id}',
                    body=f'Send message to {contact.phone_number}',
                    is_processed=False
                )

                SMS.objects.create(
                    contact=contact,
                    email=email,
                    message=f'This is a test message for {message_id} sent from {settings.ENVIRONMENT}',
                    text_id=f'text-{message_id}',
                    phone_number=f'+373{message_id[-7:]}',
                    direction='Inbound',
                    status='Sent',
                    is_processed=False
                )

            self.stdout.write(self.style.SUCCESS('Successfully seeded DB with data.'))
        else:
            # Notify that the user already exists and update email statuses.
            self.stdout.write(self.style.WARNING('User with pic_number 15372010 already exists.'))

            all_email_for_user = Email.objects.filter(user=user).all()
            for email in all_email_for_user:
                email.is_processed = False
                email.save()

            self.stdout.write(self.style.SUCCESS('Changed all emails is_processed for User to False'))




