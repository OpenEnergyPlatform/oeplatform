"""
Backfill ReviewRound rows from existing PeerReview.review blobs (Phase 1).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Best-effort reconstruction: legacy reviews never recorded round boundaries, so
``reconstruct_rounds_from_review`` flattens the merged blob, orders by timestamp
and splits at role changes. Reviews already having rounds are skipped (idempotent).
Reverse deletes all rounds; the source ``review`` JSON is untouched, so it is safe.
"""  # noqa: E501

from django.db import migrations

# Pure, unit-tested helper (dataedit/tests/test_peer_review_projection.py). Safe
# to import in this one-shot data migration.
from dataedit.peer_review.projection import reconstruct_rounds_from_review


def backfill_rounds(apps, schema_editor):
    PeerReview = apps.get_model("dataedit", "PeerReview")
    ReviewRound = apps.get_model("dataedit", "ReviewRound")

    for opr in PeerReview.objects.all():
        if ReviewRound.objects.filter(opr=opr).exists():
            continue

        rounds = reconstruct_rounds_from_review(opr.review)
        if not rounds:
            continue

        total = len(rounds)
        for rnd in rounds:
            is_last = rnd["sequence"] == total
            finished = bool(is_last and opr.is_finished)
            role = rnd["role"]
            actor_id = opr.reviewer_id if role == "reviewer" else opr.contributor_id
            ReviewRound.objects.create(
                opr=opr,
                sequence=rnd["sequence"],
                role=role,
                actor_id=actor_id,
                action="FINISHED" if finished else "SUBMITTED",
                field_reviews=rnd["field_reviews"],
                sets_finished=finished,
            )


def delete_rounds(apps, schema_editor):
    ReviewRound = apps.get_model("dataedit", "ReviewRound")
    ReviewRound.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("dataedit", "0046_add_reviewround"),
    ]

    operations = [
        migrations.RunPython(backfill_rounds, delete_rounds),
    ]
