"""The profile's Reviews tab loads none of the review page's scripts.

It used to load `opr_reviewer.js`, first as a classic script the browser
refused ("Cannot use import statement outside a module"), then as a module
(#2634) whose review-page handlers logged errors here and which never bound
the tab's Delete. Since #2658 the tab binds only its Delete, in its own small
script (#2674).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from base.tests import TestViewsTestCase


class ReviewsTabScriptTest(TestViewsTestCase):
    def test_the_tab_loads_none_of_the_review_pages_scripts(self):
        html = self.get(
            "login:reviews", kwargs={"user_id": self.user.pk}, logged_in=True
        ).content.decode()

        self.assertNotRegex(html, r"<script\b[^>]*peer_review/")
