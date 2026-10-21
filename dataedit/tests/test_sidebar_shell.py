"""The sidebar shell's head carries no stray text.

A `^` before the vite HMR client in `base/base-sidebar.html` rendered as a
visible caret above the navbar of the table view whenever compression was
off, as in development. Compression swallows it, which is why it is tested
with compression switched off.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re

from django.test import override_settings

from dataedit.tests.test_dataset_sidebar import SidebarFixture
from modelview.tests.html import text


def head_text(html):
    """The text in `<head>` outside any tag, scripts and styles left out."""
    head = re.search(r"<head\b.*?</head>", html, re.DOTALL | re.IGNORECASE).group(0)
    head = re.sub(r"<(script|style)\b.*?</\1>", "", head, flags=re.DOTALL)
    return text(re.sub(r"<!--.*?-->", "", head, flags=re.DOTALL))


@override_settings(COMPRESS_ENABLED=False)
class SidebarShellHeadTest(SidebarFixture):
    def test_the_table_view_head_has_no_stray_text(self):
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("^", head_text(response.content.decode()))
