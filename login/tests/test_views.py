"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import TestCase
from django.urls import reverse

from base.tests import get_app_reverse_lookup_names_and_kwargs
from login.models import GroupMembership, UserGroup
from login.models import myuser as User


class TestViewsLogin(TestCase):
    """Call all (most) views"""

    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()

        # create test user
        cls.user = User.objects.create_user(  # type: ignore
            name="test", email="test@test.test", affiliation="test"
        )
        cls.group = UserGroup.objects.create()
        GroupMembership.objects.create(user=cls.user, group=cls.group)

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        cls.group.delete()
        super(TestCase, cls).tearDownClass()

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET
        """

        default_kwargs = {"user_id": self.user.pk, "group_id": self.group.pk}

        self.client.force_login(self.user)

        errors = []
        for name, kwarg_names in sorted(
            get_app_reverse_lookup_names_and_kwargs("login").items()
        ):
            if name in {
                "login:password_reset_confirm",
                "login:account-delete",
                "login:detach",
                "login:group-partial-edit-form",
                "login:delete_peer_review_simple",
                "login:group-leave",  # cannot leave beacuase only member
                "login:metadata-review-badge-icon",  # we have no table in this testyet
            }:
                # skip
                continue
            resp = None
            try:
                kwargs = {k: default_kwargs[k] for k in kwarg_names}
                url = reverse(name, kwargs=kwargs)
                resp = self.client.get(path=url)
                self.assertTrue(resp.status_code < 400, msg=resp.status_code)
            except Exception as exc:
                errors.append(f"Failed view {name}: {exc}")

        if errors:
            raise Exception("\n".join(errors))
