"""A research project page that does not exist is a 404, not a 500.

The project pages are JSON files read by id; an id no file carries used to
index an empty list and take the request down with an `IndexError`.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from base.tests import TestViewsTestCase


class ProjectDetailTest(TestViewsTestCase):
    def test_a_known_project_answers(self):
        self.get("base:project_detail", kwargs={"project_id": "sirop"})

    def test_an_unknown_project_is_not_found(self):
        self.get(
            "base:project_detail",
            kwargs={"project_id": "no-such-project"},
            expect_status=404,
        )
