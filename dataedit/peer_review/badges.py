"""
BadgeService — suggest a peer-review badge, with a swappable scoring policy.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Phase 2 S5. The *policy* for how a badge is calculated (and which fields matter)
is still being decided, so it is isolated behind a tiny strategy seam:

    BadgeStrategy = Callable[[metadata, schema], Optional[PeerReviewBadge]]

To change the calculation, either:
  * edit / replace ``cumulative_tier_strategy`` below, or
  * point ``DEFAULT_BADGE_STRATEGY`` at a different function, or
  * pass ``strategy=...`` to ``BadgeService(...)`` at the call site.

Nothing else in the codebase needs to change when the policy changes — the
service, the finish flow and the tests all go through this seam.
"""  # noqa: E501

from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Set, Tuple

from oemetadata.v2.v20.schema import OEMETADATA_V20_SCHEMA

from dataedit.peer_review.metadata_serializer import get_all_field_descriptions
from dataedit.utils import PeerReviewBadge

# A strategy maps (metadata, schema) -> a badge or None. Pure; no DB, no request.
BadgeStrategy = Callable[[dict, dict], Optional[PeerReviewBadge]]

# Badge tiers from lowest to highest.
TIER_ORDER = [
    PeerReviewBadge.IRON,
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
    if schema is None:
        schema = OEMETADATA_V20_SCHEMA

    descriptions = get_all_field_descriptions(schema)
    tiers = {tier: [] for tier in TIER_ORDER}
    for path, info in descriptions.items():
        badge = normalize_badge(info.get("badge"))
        if badge in tiers:
            tiers[badge].append(path)

    # de-dupe + stable order
    for t in tiers:
        tiers[t] = sorted(set(tiers[t]))
    return tiers


# --------------------------------------------------------------------------- #
# the default policy — REPLACE/EDIT THIS to change how badges are calculated
# --------------------------------------------------------------------------- #
# def cumulative_tier_strategy(metadata, schema) -> PeerReviewBadge:
#     """Award the highest tier whose fields (and all lower tiers') are present.

#     Cumulative: a Silver field only counts once every Bronze field is present,
#     etc. Stops at the first tier with a gap. Returns IRON if Bronze is not met.

#     This is a first, deliberately-simple policy — the real weighting of "which
#     fields matter most" is still open, so expect to rewrite this function.
#     """
#     tiers = fields_by_tier(schema)
#     earned = PeerReviewBadge.IRON
#     cumulative = []
#     for tier in TIER_ORDER:
#         tier_paths = tiers.get(tier, [])
#         if not tier_paths:
#             # A tier with no declared requirements cannot be earned (and must not
#             # auto-upgrade from a lower tier).
#             continue
#         cumulative += tier_paths
#         if all(field_is_present(metadata, path) for path in cumulative):
#             earned = tier
#         else:
#             break
#     return earned


# ---------------------------------------------------------------------------
# 2. Review datamodel → ok-field extraction
# ---------------------------------------------------------------------------
_INDEX_RE = re.compile(r"\.\d+(?=\.|$)")


def normalize_review_key(review_key: str) -> str:
    """
    Map a review instance key to the schema path.
    'resources.0.title'                -> 'resources.title'
    'resources.0.schema.fields.2.name' -> 'resources.schema.fields.name'
    """
    if not review_key:
        return review_key
    return _INDEX_RE.sub("", review_key)


def _last_field_review_state(field_review) -> str:
    """
    OPR projection: fieldReview is list per round, oldest first.
    Consensus rule: last contribution wins.
    """
    if isinstance(field_review, list):
        fr = field_review[-1] if field_review else {}
    else:
        fr = field_review or {}
    if not isinstance(fr, dict):
        return ""
    return str(fr.get("state", "")).strip().lower()


def extract_ok_fields(review_data: dict) -> Set[str]:
    """
    From PeerReview.review datamodel, return schema-normalized keys
    with state == 'ok'.
    """
    ok: Set[str] = set()
    if not isinstance(review_data, dict):
        return ok
    for entry in review_data.get("reviews", []) or []:
        key = entry.get("key")
        if not key:
            continue
        if _last_field_review_state(entry.get("fieldReview")) == "ok":
            ok.add(normalize_review_key(key))
    return ok


def extract_field_states(review_data: dict) -> Dict[str, str]:
    """schema_key -> last state ('ok'|'suggestion'|'rejected'|...)."""
    states: Dict[str, str] = {}
    if not isinstance(review_data, dict):
        return states
    for entry in review_data.get("reviews", []) or []:
        key = entry.get("key")
        if not key:
            continue
        states[normalize_review_key(key)] = _last_field_review_state(
            entry.get("fieldReview")
        )
    return states


# ---------------------------------------------------------------------------
# 3. Review-state cumulative tier strategy
# ---------------------------------------------------------------------------
def review_based_cumulative_tier_strategy(
    review_data: dict,
    schema: dict | None = None,
) -> Optional[PeerReviewBadge]:
    """
    Award the highest tier whose fields AND all lower tiers are state 'ok'.

    - iron fields ok            -> IRON
    - iron + bronze ok          -> BRONZE
    - iron + bronze + silver ok -> SILVER
    - ...
    - silver ok but bronze NOT  -> returns None (fails at bronze)

    Returns None if even iron is not fully satisfied.
    """
    tiers = fields_by_tier(schema or OEMETADATA_V20_SCHEMA)
    ok_fields = extract_ok_fields(review_data)

    earned: Optional[PeerReviewBadge] = None

    for tier in TIER_ORDER:
        required = tiers.get(tier, [])
        if not required:
            # tier with no declared requirements must not auto-upgrade
            continue
        if all(req in ok_fields for req in required):
            earned = tier
        else:
            break  # cumulative stop – lower tier missing
    return earned


def review_based_cumulative_tier_strategy_details(
    review_data: dict,
    schema: dict | None = None,
) -> Tuple[Optional[PeerReviewBadge], dict]:
    """
    Same as review_based_cumulative_tier_strategy(), but returns diagnostics:
    (earned_badge_or_None, {
        'failed_at': PeerReviewBadge|None,
        'missing': {tier: [fields...]},
        'ok_fields': set(...),
        'required_by_tier': {...}
    })
    """
    tiers = fields_by_tier(schema or OEMETADATA_V20_SCHEMA)
    ok_fields = extract_ok_fields(review_data)

    earned: Optional[PeerReviewBadge] = None
    failed_at: Optional[PeerReviewBadge] = None
    missing: Dict[PeerReviewBadge, List[str]] = {}

    for tier in TIER_ORDER:
        required = set(tiers.get(tier, []))
        if not required:
            continue
        not_ok = sorted(required - ok_fields)
        if not_ok:
            failed_at = tier
            missing[tier] = not_ok
            break
        earned = tier

    return earned, {
        "earned": earned,
        "failed_at": failed_at,
        "missing": missing,
        "ok_fields": ok_fields,
        "required_by_tier": tiers,
    }


def cumulative_tier_strategy(
    metadata_or_review, schema=None
) -> Optional[PeerReviewBadge]:
    """
    Drop-in replacement for the old cumulative_tier_strategy.

    - If input looks like PeerReview.review ({'reviews': [...]})
      → review-state based, iron → platinum, cumulative.
    - Else → legacy metadata-presence path.

    Returns the earned PeerReviewBadge, or None if no requirements are met.
    """
    # Detect PeerReview.review shape
    if isinstance(metadata_or_review, dict) and "reviews" in metadata_or_review:
        return review_based_cumulative_tier_strategy(metadata_or_review, schema)

    # ---- LEGACY: metadata presence path ----
    if schema is None:
        schema = OEMETADATA_V20_SCHEMA

    tiers_legacy = fields_by_tier(schema)

    earned: Optional[PeerReviewBadge] = None
    cumulative: List[str] = []
    for tier in TIER_ORDER:
        tier_paths = tiers_legacy.get(tier, [])
        if not tier_paths:
            continue
        cumulative += tier_paths
        if all(field_is_present(metadata_or_review, path) for path in cumulative):
            earned = tier
        else:
            break
    return earned


DEFAULT_BADGE_STRATEGY: BadgeStrategy = cumulative_tier_strategy


def badge_label(badge: Optional[PeerReviewBadge]) -> str:
    """Human-readable badge label (e.g. ``"Bronze"``) or empty string."""
    if badge is None:
        return ""
    return badge.name.capitalize()


def apply_badge_to_metadata(metadata: dict, badge: Optional[PeerReviewBadge]) -> dict:
    """Persist the badge under ``metadata["review"]["badge"]``."""
    review = metadata.get("review")

    # If it doesn't exist, OR if it exists but is a string/other type, reset it
    # to an empty dict
    if not isinstance(review, dict):
        review = {}
        metadata["review"] = review

    if badge is None:
        review.pop("badge", None)
    else:
        review["badge"] = badge_label(badge)
    return metadata


def apply_badge_to_review(review: dict, badge: Optional[PeerReviewBadge]) -> dict:
    """Persist the badge onto the review datamodel."""
    review = review or {}
    if badge is None:
        review.pop("badge", None)
        review.pop("grantedBadge", None)
    else:
        label = badge_label(badge)
        review["badge"] = label
        review["grantedBadge"] = label
    return review


class BadgeService:
    """Suggest / resolve the badge for a finished review."""

    def __init__(self, strategy: Optional[BadgeStrategy] = None):
        self.strategy = strategy or DEFAULT_BADGE_STRATEGY

    def suggest_badge(self, metadata, schema=None) -> Optional[PeerReviewBadge]:
        return self.strategy(metadata, schema or OEMETADATA_V20_SCHEMA)

    def resolve_final_badge(
        self, metadata, reviewer_choice=None, schema=None
    ) -> Optional[PeerReviewBadge]:
        """The reviewer's explicit choice wins; otherwise suggest badge."""
        return normalize_badge(reviewer_choice) or self.suggest_badge(metadata, schema)
