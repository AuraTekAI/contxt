# Generated by Django 5.0.8 on 2024-08-28 09:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_botaccount"),
        ("core", "0002_processeddata"),
        ("process_emails", "0002_email_bot_alter_email_message_id_and_more"),
        ("sms_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sms",
            name="bot",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="accounts.botaccount",
            ),
        ),
        migrations.AddIndex(
            model_name="sms",
            index=models.Index(fields=["bot"], name="sms_bot_id_7860cc_idx"),
        ),
    ]
