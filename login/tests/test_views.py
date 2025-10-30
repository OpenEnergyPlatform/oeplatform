"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from base.tests import TestViewsTestCase


class TestViewsLogin(TestViewsTestCase):
    """Call all (most) views"""

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET
        """

        # "login:password_reset_confirm",
        # "login:account-delete",
        # "login:group-partial-edit-form",
        # "login:delete_peer_review_simple",
        # "login:group-leave",  # cannot leave beacuase only member
        # "login:metadata-review-badge-icon",  # we have no table in this testyet
        group_id = int(self.group.pk)
        user_id = int(self.user.pk)

        self.get("login:count-group-memberships", kwargs={"group_id": group_id})
        self.get("login:edit", kwargs={"user_id": user_id}, logged_in=True)
        self.get("login:group-create", logged_in=True)
        self.get("login:group-edit", kwargs={"group_id": group_id}, logged_in=True)
        self.get("login:groups", kwargs={"user_id": user_id})
        self.get(
            "login:partial-group-invite", kwargs={"group_id": group_id}, logged_in=True
        )
        self.get(
            "login:partial-group-membership",
            kwargs={"group_id": group_id},
            logged_in=True,
        )
        self.get("login:partial-groups", kwargs={"user_id": user_id})
        self.get("login:password_reset")
        self.get("login:password_reset_complete")
        self.get("login:password_reset_done")
        self.get("login:profile", kwargs={"user_id": user_id})
        self.get("login:redirect")
        self.get("login:reset-token", logged_in=True)
        self.get("login:reviews", kwargs={"user_id": user_id})
        self.get("login:settings", kwargs={"user_id": user_id})
        self.get("login:tables", kwargs={"user_id": user_id})
