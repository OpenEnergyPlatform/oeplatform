"""The profile's Reviews tab loads the reviewer script as an ES module.

`opr_reviewer.js` starts with `import` statements, so loaded as a classic
script the browser refuses it on every visit to the tab with "Cannot use
import statement outside a module".

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re

from base.tests import TestViewsTestCase


class ReviewsTabScriptTest(TestViewsTestCase):
    def test_the_reviewer_script_is_a_module(self):
        html = self.get(
            "login:reviews", kwargs={"user_id": self.user.pk}, logged_in=True
        ).content.decode()

        tags = re.findall(r"<script\b[^>]*opr_reviewer[^>]*>", html)
        self.assertEqual(len(tags), 1, tags)
        self.assertRegex(tags[0], r'\btype="module"')
