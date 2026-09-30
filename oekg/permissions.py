"""Who may write a scenario bundle, and what happens to that record.

The rule is asked by every mutating endpoint, because ownership is asked in
half a dozen places -- sub-resources, the two-step delete, replace -- and a rule
spelled out at each of them would drift at the first change. When the group
system is connected to bundles, this is the place that learns about it.

The delete's counterpart lives here too: ownership records are removed with
the bundle they describe, which the platform has never done.

Two properties are deliberate rather than incidental:

- **Ownership is asked of the access-control model, not compared against a
  creator.** Multi-owner bundles already exist -- an admin command adds a
  second owner -- so a single-owner comparison would be wrong today, not just
  after some future change.
- **A bundle with no ownership record is administrator-only.** Records of
  unknown provenance fail closed. That is the platform's existing behaviour for
  these bundles, kept on purpose rather than inherited by accident.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging

from django.db import transaction

from factsheet.models import ScenarioBundleAccessControl

logger = logging.getLogger("oeplatform")


def may_write_bundle(user, uid: str) -> bool:
    """Whether ``user`` may change the bundle ``uid``."""
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_admin", False):
        return True
    return ScenarioBundleAccessControl.user_has_access(user, uid)


def forget_ownership(uid: str) -> bool:
    """Remove the records saying who owns ``uid``. Returns whether it worked.

    Called after a bundle has been deleted, because ownership data that
    outlives the thing it describes is the platform's existing behaviour and is
    not defensible: the rows accumulate, they name a bundle nobody can read,
    and the next bundle minted at that identifier -- which cannot happen today,
    but is exactly the kind of thing a later change makes possible -- would
    inherit an owner nobody granted.

    **Never raises.** The graph has already committed by the time this runs, so
    a failure here cannot be answered with an error without denying a delete
    that happened. A leftover row is inert: it grants access to nothing,
    because every endpoint checks the graph for the bundle first.
    """
    try:
        # A savepoint, for the same reason the history writer takes one: a
        # rejected statement caught here would otherwise poison the surrounding
        # transaction and surface at the next query, far from its cause.
        with transaction.atomic():
            ScenarioBundleAccessControl.objects.filter(bundle_id=uid).delete()
    except Exception:
        logger.exception(
            "OEKG bundle %s was deleted from the graph but its ownership rows "
            "could not be removed. They now name a bundle that does not exist.",
            uid,
        )
        return False
    return True
