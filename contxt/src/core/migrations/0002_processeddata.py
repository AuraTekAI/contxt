# Generated by Django 5.0.8 on 2024-08-28 09:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_botaccount"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProcessedData",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("module_name", models.CharField(db_index=True, max_length=50)),
                (
                    "original_message_id",
                    models.CharField(
                        blank=True, db_index=True, max_length=255, null=True
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("processed", "Processed"), ("pending", "Pending")],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("processed_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "bot",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="accounts.botaccount",
                    ),
                ),
            ],
            options={
                "verbose_name": "processed_data",
                "verbose_name_plural": "processed_data",
                "db_table": "processed_data",
                "indexes": [
                    models.Index(
                        fields=["bot", "module_name", "status"],
                        name="processed_d_bot_id_e35352_idx",
                    ),
                    models.Index(
                        fields=["processed_at"], name="processed_d_process_33bb62_idx"
                    ),
                    models.Index(
                        fields=["created_at"], name="processed_d_created_8ae124_idx"
                    ),
                    models.Index(
                        fields=["bot", "status"], name="processed_d_bot_id_1b91e2_idx"
                    ),
                ],
            },
        ),
    ]
