"""
BadgeService — suggest a peer-review badge, with a swappable scoring policy.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Phase 2 S5. The *policy* for how a badge is calculated (and which fields matter)
is still being decided, so it is isolated behind a tiny strategy seam:

    BadgeStrategy = Callable[[metadata, schema], PeerReviewBadge]

To change the calculation, either:
  * edit / replace ``cumulative_tier_strategy`` below, or
  * point ``DEFAULT_BADGE_STRATEGY`` at a different function, or
  * pass ``strategy=...`` to ``BadgeService(...)`` at the call site.

Nothing else in the codebase needs to change when the policy changes — the
service, the finish flow and the tests all go through this seam.
"""  # noqa: E501

from typing import Callable, Optional

from oemetadata.v2.v20.schema import OEMETADATA_V20_SCHEMA

from dataedit.peer_review.metadata_serializer import get_all_field_descriptions
from dataedit.utils import PeerReviewBadge

# A strategy maps (metadata, schema) -> a badge. Pure; no DB, no request.
BadgeStrategy = Callable[[dict, dict], PeerReviewBadge]

# Badge tiers from lowest to highest. IRON is the fallback when no tier is met.
TIER_ORDER = [
    PeerReviewBadge.BRONZE,
    PeerReviewBadge.SILVER,
    PeerReviewBadge.GOLD,
    PeerReviewBadge.PLATINUM,
]


# --------------------------------------------------------------------------- #
# small, reusable building blocks (each is easy to swap independently)
# --------------------------------------------------------------------------- #
def normalize_badge(name) -> Optional[PeerReviewBadge]:
    """Map a badge label from any source (schema "Platinum", UI "platin", enum
    "PLATINUM") to the canonical ``PeerReviewBadge`` — or None if unknown."""
    if not name:
        return None
    key = str(name).strip().upper()
    if key == "PLATIN":  # the UI radios still emit "platin"
        key = "PLATINUM"
    return PeerReviewBadge.__members__.get(key)


_EMPTY_SENTINELS = {"", "none", "null", "[]", "{}", "nan"}


def is_filled(value) -> bool:
    """Whether a metadata value counts as provided. Swap this to change what
    'filled' means (e.g. treat bounding-box 0 as empty)."""
    if value is None:
        return False
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return str(value).strip().lower() not in _EMPTY_SENTINELS


def _resolve_path(metadata, dotted_path):
    """Tolerant lookup of a schema field path in metadata. Descends into the
    first element of any list (e.g. ``resources`` -> ``resources[0]``), which is
    how OEMetadata v2 nests resource fields."""
    current = metadata
    for part in dotted_path.split("."):
        if isinstance(current, list):
            if not current:
                return None
            current = current[0]
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    if isinstance(current, list) and len(current) == 1:
        return current[0]
    return current


def field_is_present(metadata, dotted_path) -> bool:
    return is_filled(_resolve_path(metadata, dotted_path))


def fields_by_tier(schema) -> dict:
    """Group schema field paths by their declared ``badge`` tier.

    Reads the per-field ``badge`` attribute via the metadata serializer, so it
    follows the schema exactly. Returns ``{PeerReviewBadge: [dotted paths]}``.
    """
    descriptions = get_all_field_descriptions(schema)
    tiers = {tier: [] for tier in TIER_ORDER}
    for path, info in descriptions.items():
        badge = normalize_badge(info.get("badge"))
        if badge in tiers:
            tiers[badge].append(path)
    return tiers


# --------------------------------------------------------------------------- #
# the default policy — REPLACE/EDIT THIS to change how badges are calculated
# --------------------------------------------------------------------------- #
def cumulative_tier_strategy(metadata, schema) -> PeerReviewBadge:
    """Award the highest tier whose fields (and all lower tiers') are present.

    Cumulative: a Silver field only counts once every Bronze field is present,
    etc. Stops at the first tier with a gap. Returns IRON if Bronze is not met.

    This is a first, deliberately-simple policy — the real weighting of "which
    fields matter most" is still open, so expect to rewrite this function.
    """
    tiers = fields_by_tier(schema)
    earned = PeerReviewBadge.IRON
    cumulative = []
    for tier in TIER_ORDER:
        tier_paths = tiers.get(tier, [])
        if not tier_paths:
            # A tier with no declared requirements cannot be earned (and must not
            # auto-upgrade from a lower tier).
            continue
        cumulative += tier_paths
        if all(field_is_present(metadata, path) for path in cumulative):
            earned = tier
        else:
            break
    return earned


DEFAULT_BADGE_STRATEGY: BadgeStrategy = cumulative_tier_strategy


def badge_label(badge: PeerReviewBadge) -> str:
    """Human-readable badge label (e.g. ``"Bronze"``). ``Table`` and the
    profile/dataview cards upper-case it when matching, so case is not critical."""
    return badge.name.capitalize()


def apply_badge_to_metadata(metadata: dict, badge: PeerReviewBadge) -> dict:
    """Persist the badge under ``metadata["review"]["badge"]`` in the form
    ``Table.get_review_badge_from_table_metadata`` expects (it upper-cases and
    matches the enum name)."""

    # Safely get the existing review data
    review = metadata.get("review")

    # If it doesn't exist, OR if it exists but is a string/other type, reset it
    # to an empty dict
    if not isinstance(review, dict):
        review = {}
        metadata["review"] = review

    review["badge"] = badge_label(badge)
    return metadata


def apply_badge_to_review(review: dict, badge: PeerReviewBadge) -> dict:
    """Persist the badge onto the review datamodel. The dataview "Latest review
    completed" card reads ``PeerReview.review["badge"]`` (see views.py), so the
    award must land here too — not only in the table metadata."""
    review = review or {}
    label = badge_label(badge)
    review["badge"] = label
    review["grantedBadge"] = label
    return review


class BadgeService:
    """Suggest / resolve the badge for a finished review."""

    def __init__(self, strategy: Optional[BadgeStrategy] = None):
        self.strategy = strategy or DEFAULT_BADGE_STRATEGY

    def suggest_badge(self, metadata, schema=None) -> PeerReviewBadge:
        return self.strategy(metadata, schema or OEMETADATA_V20_SCHEMA)

    def resolve_final_badge(
        self, metadata, reviewer_choice=None, schema=None
    ) -> PeerReviewBadge:
        """The reviewer's explicit choice wins (decision §D: auto + override);
        otherwise fall back to the auto-suggestion."""
        return normalize_badge(reviewer_choice) or self.suggest_badge(metadata, schema)
