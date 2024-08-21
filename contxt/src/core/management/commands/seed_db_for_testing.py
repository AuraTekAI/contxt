
from contxt.utils.constants import SMS_TABLE_SEED_DATA
from core.models import SMS
from process_emails.models import Email
from accounts.models import User
from core.models import Contact

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.transaction import atomic
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seed DB with data to enable testing the implemented modules.'

    @atomic
    def handle(self, *args, **kwargs):
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
            self.stdout.write(self.style.SUCCESS('Created user with pic_number 15372010.'))
        else:
            self.stdout.write(self.style.WARNING('User with pic_number 15372010 already exists.'))

        if not Contact.objects.filter(user=user).all():
            contact, contact_created = Contact.objects.get_or_create(
                user=user,
                defaults={
                    'contact_name': f'Contact for {user.name}',
                    'phone_number': f'+3731234568',
                    'email': f'{user.user_name}@example.com' if user.custom_email is None else user.custom_email,
                }
            )

            if contact_created:
                self.stdout.write(self.style.SUCCESS(f'Created contact for user {user.name}.'))
            else:
                self.stdout.write(self.style.WARNING(f'Contact for user {user.name} already exists.'))

        for message_id in SMS_TABLE_SEED_DATA.keys():
            email = Email.objects.create(
                user=user,
                message_id=message_id,
                sent_date_time=timezone.now(),
                subject=f'Subject {message_id}',
                body=f'Body content for {message_id}',
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
