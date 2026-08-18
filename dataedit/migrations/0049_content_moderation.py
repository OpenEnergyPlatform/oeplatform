"""
SPDX-FileCopyrightText: 2026 Open Energy Platform contributors
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0048_drop_manager_prev_next_fks"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentReport",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("table_name", models.CharField(max_length=1000)),
                ("subject", models.CharField(max_length=255)),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("illegal_content", "Potentially illegal content"),
                            ("copyright", "Copyright / rights infringement"),
                            ("other", "Other"),
                        ],
                        max_length=32,
                    ),
                ),
                ("message", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("awaiting_uploader", "Awaiting uploader response"),
                            ("under_review", "Under review"),
                            ("dismissed", "No violation"),
                            ("violation", "Violation"),
                        ],
                        db_index=True,
                        default="open",
                        max_length=32,
                    ),
                ),
                ("uploader_response", models.TextField(blank=True, default="")),
                (
                    "uploader_responded_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("resolution_note", models.TextField(blank=True, default="")),
                (
                    "created",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "updated",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "reporter",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="content_reports_filed",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "resolved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="content_reports_resolved",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "table",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="content_reports",
                        to="dataedit.table",
                    ),
                ),
            ],
            options={
                "ordering": ["-created"],
            },
        ),
        migrations.CreateModel(
            name="ModerationHold",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("was_published", models.BooleanField(default=False)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="moderation_holds_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="holds",
                        to="dataedit.contentreport",
                    ),
                ),
                (
                    "table",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="moderation_hold",
                        to="dataedit.table",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserModerationWarning",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("note", models.TextField(blank=True, default="")),
                (
                    "created",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="moderation_warnings_issued",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="warnings",
                        to="dataedit.contentreport",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="moderation_warnings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created"],
            },
        ),
    ]
