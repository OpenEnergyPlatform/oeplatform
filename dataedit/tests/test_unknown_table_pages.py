"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

A page naming a table that does not exist answers 404, not 500.

The pages used `api.utils.table_or_404`, which raises an `APIError` that only
the API turns into a 404. On production a deleted table's page answered 500,
4,658 times in the Django log between 2026-09-21 and 2026-11-28.
"""  # noqa: 501

from base.tests import TestViewsTestCase

UNKNOWN = "no_such_table_anywhere"

# Every route below `/database/tables/<table>` that looks the table up.
GET_ROUTES = [
    ("view", {}),
    ("table-permission", {}),
    ("meta_edit", {}),
    ("table-graph", {}),
    ("table-map", {"maptype": "latlon"}),
    ("peer_review_create", {}),
    ("peer_review_reviewer", {"review_id": 1}),
    ("peer_review_contributor", {"review_id": 1}),
]
POST_ROUTES = [
    ("table-view-save", {}),
    ("table-view-set-default", {"view_id": 1}),
    ("table-view-delete-default", {"view_id": 1}),
]


class UnknownTablePageTest(TestViewsTestCase):
    def test_get_routes_answer_404(self):
        for name, extra in GET_ROUTES:
            for logged_in in (False, True):
                if not logged_in and name != "view":
                    continue  # the others send an anonymous caller to log in
                with self.subTest(route=name, logged_in=logged_in):
                    self.get(
                        f"dataedit:{name}",
                        kwargs={"table": UNKNOWN, **extra},
                        logged_in=logged_in,
                        expect_status=404,
                    )

    def test_post_routes_answer_404(self):
        for name, extra in POST_ROUTES:
            with self.subTest(route=name):
                self.post(
                    f"dataedit:{name}",
                    kwargs={"table": UNKNOWN, **extra},
                    logged_in=True,
                    expect_status=404,
                )
