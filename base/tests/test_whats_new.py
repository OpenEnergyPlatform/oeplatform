"""The "What's new" page (#2382): the newest released changelog's `## Highlights`.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import tempfile
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from base.helper import latest_release_highlights

CHANGELOG = """# Changes to the oeplatform code

## Highlights

{}

## Changes

- an internal change users never see
"""

HIGHLIGHTS = "<ul><li>Datasets start as drafts</li></ul>"
VERSION = Path(settings.BASE_DIR, "VERSION").read_text().strip()


class LatestReleaseHighlightsTest(SimpleTestCase):
    def highlights(self, **files):
        with tempfile.TemporaryDirectory() as directory:
            for name, highlights in files.items():
                Path(directory, name).write_text(CHANGELOG.format(highlights))
            # The cache keys on the directory, and every one here is new.
            return latest_release_highlights(directory)

    def test_the_newest_release_by_number_wins(self):
        html = self.highlights(
            **{"1_9_0.md": "- nine", "1_10_0.md": "- ten", "1_2_0.md": "- two"}
        )
        self.assertEqual(html.strip(), "<ul>\n<li>ten</li>\n</ul>")

    def test_only_the_highlights_section_is_shown(self):
        html = self.highlights(**{"1_10_0.md": "- **New** list"})
        self.assertEqual(
            html.strip(), "<ul>\n<li><strong>New</strong> list</li>\n</ul>"
        )

    def test_a_release_without_highlights_is_skipped(self):
        html = self.highlights(
            **{
                "1_10_0.md": "- ten",
                "1_10_1.md": "",
                "1_10_2.md": "<!-- the template's comment, never filled -->",
            }
        )
        self.assertEqual(html.strip(), "<ul>\n<li>ten</li>\n</ul>")

    def test_the_next_release_is_not_out_yet(self):
        self.assertEqual(self.highlights(**{"current.md": "- coming"}), "")


class WhatsNewPagesTest(TestCase):
    def get(self, name, highlights):
        with mock.patch(
            "base.views.latest_release_highlights", return_value=highlights
        ):
            return self.client.get(reverse(name)).content.decode()

    def test_the_page_shows_the_highlights(self):
        page = self.get("base:whats-new", HIGHLIGHTS)
        self.assertIn("<li>Datasets start as drafts</li>", page)

    def test_the_page_without_highlights_says_so(self):
        self.assertIn("No release highlights yet.", self.get("base:whats-new", ""))

    def test_the_homepage_links_the_page_when_there_is_news(self):
        self.assertIn("See what's new", self.get("base:home", HIGHLIGHTS))
        self.assertNotIn("See what's new", self.get("base:home", ""))

    def test_no_page_names_the_running_release(self):
        # The pages do not tell a visitor which release production runs.
        for name in ("base:home", "base:whats-new"):
            self.assertNotIn(VERSION, self.get(name, HIGHLIGHTS), name)
