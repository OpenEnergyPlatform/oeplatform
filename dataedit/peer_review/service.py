"""
ReviewService — single orchestration entry point for OPR mutations.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Phase 2 S3/S4: the create-vs-update branching lives here, and submit/finish now
record a ``ReviewRound`` (the append-only per-turn log) and rebuild
``PeerReview.review`` as a projection of all rounds. ``merge_field_reviews`` and
the old "extend the reviewer payload with stored contributor reviews" hack are
gone — round history + ``compute_round_delta`` replace them.

Drafts (``reviewType="save"``) do NOT create a round; they store the working
payload as-is. Status/turn/snapshot are still delegated to the model
``PeerReview.save(review_type=...)`` / ``.update(review_type=...)``.

HTTP concerns stay in the views: the service raises ``ContributorNotFoundError``
for the "no table holder" case and the view maps it to a 400.

NOTE: existing reviews must be backfilled into rounds (migration 0047) before this
write path runs, otherwise an ongoing review's earlier history (which lived only
in the old ``review`` blob) is not yet represented as rounds.
"""  # noqa: E501

from dataedit.helper import recursive_update
from dataedit.metadata import load_metadata_from_db, save_metadata_to_db
from dataedit.models import (
    PeerReview,
    PeerReviewManager,
    ReviewDataStatus,
    Reviewer,
    ReviewRound,
    Table,
)
from dataedit.peer_review.badges import (
    BadgeService,
    apply_badge_to_metadata,
    apply_badge_to_review,
)
from dataedit.peer_review.projection import compute_round_delta, project_review


class ContributorNotFoundError(Exception):
    """No user identifies as table holder / contributor for the table."""


class ReviewService:
    """All peer-review write paths. Views call this; they do not touch the ORM
    review models directly anymore."""

    def __init__(self, table_name: str, actor):
        self.table_name = table_name
        self.actor = actor

    # ------------------------------------------------------------------ #
    # rounds + projection
    # ------------------------------------------------------------------ #
    def _rounds(self, opr) -> list:
        return list(
            opr.rounds.order_by("sequence").values(
                "sequence", "field_reviews", "sets_finished"
            )
        )

    def _record_round(self, opr, role, review_post_type, incoming_reviews, finished):
        """Append a ReviewRound for this turn and rebuild ``opr.review``.

        Only the contributions new this turn (vs prior rounds) are stored on the
        round; ``opr.review`` is then re-projected from all rounds. ``opr`` is not
        saved here — the caller's ``save``/``update`` persists ``opr.review``.
        """
        prior = self._rounds(opr)
        delta = compute_round_delta(incoming_reviews, prior)
        next_sequence = (prior[-1]["sequence"] if prior else 0) + 1
        action = (
            ReviewDataStatus.FINISHED.value
            if finished
            else ReviewDataStatus.SUBMITTED.value
        )
        ReviewRound.objects.create(
            opr=opr,
            sequence=next_sequence,
            role=role,
            actor=self.actor,
            action=action,
            field_reviews=delta,
            sets_finished=bool(finished),
        )
        opr.review = project_review(opr.review or {}, self._rounds(opr))

    # ------------------------------------------------------------------ #
    # reviewer side
    # ------------------------------------------------------------------ #
    def submit_reviewer_review(self, payload: dict, review_id=None) -> None:
        review_datamodel = payload.get("reviewData") or {}
        review_post_type = payload.get("reviewType")
        review_finished = review_datamodel.get("reviewFinished")
        incoming_reviews = review_datamodel.get("reviews", [])

        contributor = PeerReviewManager.load_contributor(table=self.table_name)
        if contributor is None:
            raise ContributorNotFoundError(
                "Failed to retrieve any user that identifies "
                f"as table holder for the current table: {self.table_name}!"
            )

        active = PeerReview.load(table=self.table_name)
        creating = active is None or active.is_finished

        if review_post_type == "save":
            # Draft: store the working payload as-is, no round recorded.
            if creating:
                self._create_opr(contributor, review_datamodel).save(review_type="save")
            else:
                active.review = review_datamodel
                active.reviewer = self.actor
                active.contributor = contributor
                active.update(review_type="save")
            return

        if creating:
            opr = self._create_opr(contributor, review_datamodel)
            opr.save()  # obtain a pk; no manager yet
            self._record_round(
                opr,
                Reviewer.REVIEWER.value,
                review_post_type,
                incoming_reviews,
                review_finished,
            )
            opr.save(review_type=review_post_type)
        else:
            opr = active
            self._record_round(
                opr,
                Reviewer.REVIEWER.value,
                review_post_type,
                incoming_reviews,
                review_finished,
            )
            opr.reviewer = self.actor
            opr.contributor = contributor
            opr.update(review_type=review_post_type)

        if review_finished is True:
            self._apply_finished(opr, reviewer_choice=payload.get("reviewBadge"))

    def _create_opr(self, contributor, review_datamodel) -> PeerReview:
        return PeerReview(
            table=self.table_name,
            is_finished=False,
            review=review_datamodel,
            reviewer=self.actor,
            contributor=contributor,
            oemetadata=load_metadata_from_db(table=self.table_name),
        )

    # ------------------------------------------------------------------ #
    # contributor side
    # ------------------------------------------------------------------ #
    def submit_contributor_review(self, payload: dict, review_id) -> None:
        review_datamodel = payload.get("reviewData") or {}
        review_post_type = payload.get("reviewType")
        review_finished = review_datamodel.get("reviewFinished")
        incoming_reviews = review_datamodel.get("reviews", [])

        opr = PeerReviewManager.get_opr_by_id(opr_id=review_id)

        if review_post_type == "save":
            opr.review = review_datamodel
            opr.update(review_type="save")
            return

        self._record_round(
            opr,
            Reviewer.CONTRIBUTOR.value,
            review_post_type,
            incoming_reviews,
            review_finished,
        )
        opr.update(review_type=review_post_type)

        if review_finished is True:
            self._apply_finished(opr, reviewer_choice=payload.get("reviewBadge"))

    # ------------------------------------------------------------------ #
    # finish: merge accepted values back into metadata
    # ------------------------------------------------------------------ #
    def _apply_finished(self, opr, reviewer_choice=None) -> None:
        """Mark the table reviewed, merge the (projected) accepted values into the
        live table metadata and the pinned snapshot, and award the badge.

        The badge is the reviewer's explicit choice if given, else the
        auto-suggestion (see ``BadgeService`` for the swappable policy)."""
        review_table = Table.load(name=self.table_name)
        review_table.set_is_reviewed()

        envelope = {"reviewData": opr.review}

        # Apply accepted values to the live metadata, then award the badge based
        # on the resulting (final) metadata.
        live_metadata = recursive_update(
            load_metadata_from_db(table=self.table_name), envelope
        )
        badge = BadgeService().resolve_final_badge(
            live_metadata, reviewer_choice=reviewer_choice
        )
        apply_badge_to_metadata(live_metadata, badge)
        save_metadata_to_db(self.table_name, live_metadata)

        # Mirror the merged values + badge into the pinned snapshot.
        opr.oemetadata = apply_badge_to_metadata(
            recursive_update(opr.oemetadata or {}, envelope), badge
        )
        # Record the badge on the review datamodel too — the dataview "Latest
        # review completed" card reads PeerReview.review["badge"].
        opr.review = apply_badge_to_review(opr.review, badge)
        opr.save()
