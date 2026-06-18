"""
ReviewService — single orchestration entry point for OPR mutations.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Phase 2, step S2: the create-vs-update branching that used to live inside
``TablePeerReviewView.post`` / ``TablePeerRreviewContributorView.post`` moves here
**1:1**. This is intentionally behavior-preserving — it still calls the existing
``PeerReview.save(review_type=...)`` / ``.update(review_type=...)`` model methods,
so the duplicate-``PeerReviewManager`` bug is *not* fixed yet (that happens in
S3/S4 together with the ``ReviewRound`` work). The 42 characterization tests stay
green across this change.

HTTP concerns stay in the views: the service raises ``ContributorNotFoundError``
for the "no table holder" case and the view maps it to a 400.
"""  # noqa: E501

from dataedit.helper import merge_field_reviews, recursive_update
from dataedit.metadata import load_metadata_from_db, save_metadata_to_db
from dataedit.models import PeerReview, PeerReviewManager, Table


class ContributorNotFoundError(Exception):
    """No user identifies as table holder / contributor for the table."""


class ReviewService:
    """All peer-review write paths. Views call this; they do not touch the ORM
    review models directly anymore."""

    def __init__(self, table_name: str, actor):
        self.table_name = table_name
        self.actor = actor

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    def _load_review_metadata(self, review_id=None) -> dict:
        """Mirror of the old ``TablePeerReviewView.load_json``: snapshot if a
        review_id is given, else the live table metadata."""
        if review_id is None:
            return load_metadata_from_db(table=self.table_name)
        opr = PeerReviewManager.get_opr_by_id(opr_id=review_id)
        return opr.oemetadata

    # ------------------------------------------------------------------ #
    # reviewer side
    # ------------------------------------------------------------------ #
    def submit_reviewer_review(self, payload: dict, review_id=None) -> None:
        """Reviewer save/submit/finish. Equivalent to the old reviewer POST
        body (minus the ``delete`` branch, which the view handles)."""
        review_data = payload
        if review_id:
            contributor_review = PeerReview.objects.filter(id=review_id).first()
            if contributor_review:
                contributor_review_data = (contributor_review.review or {}).get(
                    "reviews", []
                )
                review_data["reviewData"]["reviews"].extend(contributor_review_data)

        review_post_type = review_data.get("reviewType")
        review_datamodel = review_data.get("reviewData")
        review_finished = review_datamodel.get("reviewFinished")

        contributor = PeerReviewManager.load_contributor(table=self.table_name)
        if contributor is None:
            raise ContributorNotFoundError(
                "Failed to retrieve any user that identifies "
                f"as table holder for the current table: {self.table_name}!"
            )

        active_peer_review = PeerReview.load(table=self.table_name)
        if active_peer_review is None or active_peer_review.is_finished:
            # no active review (or the active one is finished) -> create a new one
            table_review = PeerReview(
                table=self.table_name,
                is_finished=review_finished,
                review=review_datamodel,
                reviewer=self.actor,
                contributor=contributor,
                oemetadata=load_metadata_from_db(table=self.table_name),
            )
            table_review.save(review_type=review_post_type)
        else:
            # active review exists -> merge this turn into it and update
            merged_review_data = merge_field_reviews(
                current_json=active_peer_review.review, new_json=review_datamodel
            )
            active_peer_review.review = merged_review_data
            active_peer_review.reviewer = self.actor
            active_peer_review.contributor = contributor
            active_peer_review.update(review_type=review_post_type)

        if review_finished is True:
            self._apply_finished(review_data, review_id)

    def _apply_finished(self, review_data: dict, review_id) -> None:
        """Merge accepted values back into the live + snapshot metadata and mark
        the table reviewed (old reviewer POST ``review_finished`` block)."""
        review_table = Table.load(name=self.table_name)
        review_table.set_is_reviewed()

        metadata = self._load_review_metadata(review_id=review_id)
        updated_metadata = recursive_update(metadata, review_data)
        save_metadata_to_db(self.table_name, updated_metadata)

        active_peer_review = PeerReview.load(table=self.table_name)
        if active_peer_review:
            updated_oemetadata = recursive_update(
                active_peer_review.oemetadata, review_data
            )
            active_peer_review.oemetadata = updated_oemetadata
            active_peer_review.save()

    # ------------------------------------------------------------------ #
    # contributor side
    # ------------------------------------------------------------------ #
    def submit_contributor_review(self, payload: dict, review_id) -> None:
        """Contributor reply: merge into the existing review and update.
        Equivalent to the old contributor POST body."""
        review_post_type = payload.get("reviewType")
        review_datamodel = payload.get("reviewData")
        current_opr = PeerReviewManager.get_opr_by_id(opr_id=review_id)
        merged_review = merge_field_reviews(
            current_json=current_opr.review, new_json=review_datamodel
        )
        current_opr.review = merged_review
        current_opr.update(review_type=review_post_type)
