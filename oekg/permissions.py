"""Who may write a scenario bundle.

One function, asked by every mutating endpoint, because ownership is about to
be asked in four more places -- sub-resources, the two-step delete, replace --
and a rule spelled out at each of them would drift at the first change. When
the group system is connected to bundles, this is the place that learns about
it.

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

from factsheet.models import ScenarioBundleAccessControl


def may_write_bundle(user, uid: str) -> bool:
    """Whether ``user`` may change the bundle ``uid``."""
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_admin", False):
        return True
    return ScenarioBundleAccessControl.user_has_access(user, uid)
