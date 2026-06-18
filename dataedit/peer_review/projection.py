"""
Projection of ReviewRound rows into the ``PeerReview.review`` JSON cache.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Phase 1 / Phase 2 S3: ``ReviewRound`` rows are the append-only source of truth for
the ping-pong; ``PeerReview.review`` becomes a derived cache rebuilt from them.

These functions are pure (they take plain dict/list data, not ORM objects) so they
are trivially unit-testable. The key guarantee: in the projected ``reviews`` list
every entry's ``fieldReview`` is **always a list** — one element per round that
touched that field, ordered by round ``sequence``. This removes the historical
dict-or-list ambiguity that ``merge_field_reviews`` produced.
"""  # noqa: E501

import json


def _entry_identity(category, key, field_review) -> tuple:
    """Stable identity for a single field-review contribution.

    Two contributions are "the same" if they share category, key and an
    identical ``fieldReview`` payload (timestamps included). Used to filter out
    entries the client re-sends that a previous round already recorded.
    """
    return (
        category,
        key,
        json.dumps(field_review, sort_keys=True, default=str),
    )


def compute_round_delta(incoming_reviews, prior_rounds):
    """Return only the field-review contributions that are new this turn.

    The POST payload carries the acting user's *full accumulated* review set, not
    a per-turn delta, so we diff it against everything already recorded in prior
    rounds and keep only what is genuinely new.

    Args:
        incoming_reviews: list of ``{key, category, fieldReview}`` from the POST.
            ``fieldReview`` may be a single dict or (defensively) a list.
        prior_rounds: list of round dicts (``{"field_reviews": [...]}``) already
            stored for the opr.

    Returns:
        list: new ``{key, category, fieldReview: dict}`` entries (each
            ``fieldReview`` a single dict), de-duplicated and in input order.
    """
    seen = set()
    for rnd in prior_rounds or []:
        for entry in rnd.get("field_reviews") or []:
            seen.add(
                _entry_identity(
                    entry.get("category"), entry.get("key"), entry.get("fieldReview")
                )
            )

    delta = []
    for entry in incoming_reviews or []:
        field_review = entry.get("fieldReview")
        contributions = (
            field_review if isinstance(field_review, list) else [field_review]
        )
        for one in contributions:
            identity = _entry_identity(entry.get("category"), entry.get("key"), one)
            if identity in seen:
                continue
            seen.add(identity)
            delta.append(
                {
                    "key": entry.get("key"),
                    "category": entry.get("category"),
                    "fieldReview": one,
                }
            )
    return delta


def reconstruct_rounds_from_review(review):
    """Best-effort reconstruction of rounds from a legacy merged ``review`` blob.

    Historical reviews never recorded round boundaries, so we flatten every
    ``fieldReview`` contribution, order by ``timestamp``, and split into rounds at
    each ``role`` change. Entries lacking a timestamp sort first; entries lacking a
    role collapse into the surrounding round.

    Args:
        review (dict | None): a ``PeerReview.review`` datamodel.

    Returns:
        list: ``[{"sequence": int, "role": str,
                   "field_reviews": [{key, category, fieldReview}]}]`` in order.
            ``action`` / ``actor`` / ``sets_finished`` are left to the caller.
    """
    reviews = review.get("reviews", []) if isinstance(review, dict) else []

    entries = []
    for item in reviews:
        field_review = item.get("fieldReview")
        contributions = (
            field_review if isinstance(field_review, list) else [field_review]
        )
        for one in contributions:
            if one is None:
                continue
            entries.append(
                {
                    "key": item.get("key"),
                    "category": item.get("category"),
                    "fieldReview": one,
                }
            )

    def _ts(entry):
        fr = entry["fieldReview"]
        return (fr.get("timestamp") or 0) if isinstance(fr, dict) else 0

    entries.sort(key=_ts)

    rounds = []
    current = []
    last_role = None
    for entry in entries:
        fr = entry["fieldReview"]
        role = fr.get("role") if isinstance(fr, dict) else None
        if last_role is not None and role != last_role and current:
            rounds.append((last_role, current))
            current = []
        current.append(entry)
        last_role = role
    if current:
        rounds.append((last_role, current))

    return [
        {"sequence": i, "role": role or "reviewer", "field_reviews": items}
        for i, (role, items) in enumerate(rounds, start=1)
    ]


def build_reviews_from_rounds(rounds):
    """Fold round field-reviews into the projected ``reviews`` list.

    Args:
        rounds: iterable of dicts shaped like a ``ReviewRound``:
            ``{"sequence": int, "field_reviews": [
                {"key": str, "category": str, "fieldReview": dict}, ...]}``.
            Extra keys are ignored. ``field_reviews`` defaults to an empty list.

    Returns:
        list: one entry per ``(category, key)`` first seen, shaped as
            ``{"category": str, "key": str, "fieldReview": [dict, ...]}`` where
            the inner list holds each round's contribution in ascending
            ``sequence`` order. Entry order follows first appearance.
    """
    ordered_rounds = sorted(rounds, key=lambda r: r.get("sequence", 0))

    by_key: dict[tuple, dict] = {}
    appearance_order: list[tuple] = []

    for rnd in ordered_rounds:
        for entry in rnd.get("field_reviews") or []:
            identity = (entry.get("category"), entry.get("key"))
            if identity not in by_key:
                by_key[identity] = {
                    "category": entry.get("category"),
                    "key": entry.get("key"),
                    "fieldReview": [],
                }
                appearance_order.append(identity)
            by_key[identity]["fieldReview"].append(entry.get("fieldReview"))

    return [by_key[identity] for identity in appearance_order]


def project_review(base, rounds):
    """Rebuild a full review datamodel from rounds, preserving header fields.

    Args:
        base (dict | None): the existing review datamodel whose non-``reviews``
            header fields (topic, table, dateStarted, reviewFinished, badge,
            metaMetadata, ...) should be carried over.
        rounds: see :func:`build_reviews_from_rounds`.

    Returns:
        dict: a shallow copy of ``base`` with ``reviews`` replaced by the
            projection and ``reviewFinished`` set if any round finished it.
    """
    projected = dict(base or {})
    projected["reviews"] = build_reviews_from_rounds(rounds)

    if any(r.get("sets_finished") for r in rounds):
        projected["reviewFinished"] = True

    return projected
