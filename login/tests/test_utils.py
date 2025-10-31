"""
SPDX-FileCopyrightText: Christian Winger
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import TestCase

from dataedit.models import Table
from login.models import (
    NO_PERM,
    WRITE_PERM,
    GroupMembership,
    GroupPermission,
    UserGroup,
    UserPermission,
)
from login.models import myuser as User


class TestUtils(TestCase):
    def test_user_get_tables_queryset(self):
        user_a: User = User.objects.create_user(  # type:ignore
            name="A", email="a@test.test", affiliation="test"
        )
        user_b: User = User.objects.create_user(  # type:ignore
            name="B", email="b@test.test", affiliation="test"
        )

        group_1 = UserGroup.objects.create(name="G1")
        group_2 = UserGroup.objects.create(name="G2")

        GroupMembership.objects.create(user=user_a, group=group_1)
        GroupMembership.objects.create(user=user_a, group=group_2)
        GroupMembership.objects.create(user=user_b, group=group_2)

        table_a = Table.objects.create(name="ta")
        table_b = Table.objects.create(name="tb")
        table_2 = Table.objects.create(name="t2")
        table_1a = Table.objects.create(name="t1a")

        UserPermission.objects.create(holder=user_a, table=table_a, level=WRITE_PERM)
        UserPermission.objects.create(holder=user_b, table=table_b, level=WRITE_PERM)
        UserPermission.objects.create(holder=user_a, table=table_1a, level=WRITE_PERM)
        GroupPermission.objects.create(holder=group_1, table=table_1a, level=WRITE_PERM)
        GroupPermission.objects.create(holder=group_2, table=table_2, level=NO_PERM)

        tables_a = user_a.get_tables_queryset().all().order_by("name")
        # testing: only tb is missing, t1a not duplicated
        self.assertListEqual([t.name for t in tables_a.all()], ["t1a", "t2", "ta"])

        tables_b = (
            user_b.get_tables_queryset(min_permission_level=WRITE_PERM)
            .all()
            .order_by("name")
        )
        # we only get "tb", because group levels for t2 are too low
        self.assertListEqual([t.name for t in tables_b.all()], ["tb"])
