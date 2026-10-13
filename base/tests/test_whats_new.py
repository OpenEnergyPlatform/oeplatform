"""The "What's new" page (#2382): each released changelog's `## Highlights`.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import tempfile
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from base.helper import release_highlights

CHANGELOG = """# Changes to the oeplatform code

## Highlights

{}

## Changes

- an internal change users never see
"""

RELEASE = {
    "version": "1.11.0",
    "html": "<ul><li>Datasets start as drafts</li></ul>",
    "changelog_url": "https://example.org/1_11_0.md",
}


class ReleaseHighlightsTest(SimpleTestCase):
    def highlights(self, **files):
        with tempfile.TemporaryDirectory() as directory:
            for name, highlights in files.items():
                Path(directory, name).write_text(CHANGELOG.format(highlights))
            # The cache keys on the directory, and every one here is new.
            return release_highlights(directory)

    def test_released_versions_newest_first_by_number(self):
        releases = self.highlights(
            **{"1_9_0.md": "- nine", "1_10_0.md": "- ten", "1_2_0.md": "- two"}
        )
        self.assertEqual(
            [release["version"] for release in releases], ["1.10.0", "1.9.0", "1.2.0"]
        )

    def test_only_the_highlights_section_is_shown(self):
        (release,) = self.highlights(**{"1_10_0.md": "- **New** list"})
        self.assertEqual(
            release["html"].strip(), "<ul>\n<li><strong>New</strong> list</li>\n</ul>"
        )
        self.assertTrue(
            release["changelog_url"].endswith(
                "/blob/v1.10.0/versions/changelogs/1_10_0.md"
            )
        )

    def test_a_release_without_highlights_is_left_out(self):
        releases = self.highlights(
            **{
                "1_10_0.md": "- ten",
                "1_10_1.md": "",
                "1_10_2.md": "<!-- the template's comment, never filled -->",
            }
        )
        self.assertEqual([release["version"] for release in releases], ["1.10.0"])

    def test_the_next_release_is_not_out_yet(self):
        self.assertEqual(self.highlights(**{"current.md": "- coming"}), [])

    def test_the_repositorys_changelogs_parse(self):
        for release in release_highlights():
            self.assertTrue(release["html"].strip())


class WhatsNewPagesTest(TestCase):
    def test_the_page_lists_each_release_with_its_changelog(self):
        with mock.patch("base.views.release_highlights", return_value=[RELEASE]):
            page = self.client.get(reverse("base:whats-new")).content.decode()
        self.assertIn("Version 1.11.0", page)
        self.assertIn("<li>Datasets start as drafts</li>", page)
        self.assertIn('href="https://example.org/1_11_0.md"', page)

    def test_the_page_without_releases_says_so(self):
        with mock.patch("base.views.release_highlights", return_value=[]):
            page = self.client.get(reverse("base:whats-new")).content.decode()
        self.assertIn("No release highlights yet.", page)

    def test_the_homepage_links_the_newest_release(self):
        with mock.patch("base.views.release_highlights", return_value=[RELEASE]):
            page = self.client.get(reverse("base:home")).content.decode()
        self.assertIn("What's new in version 1.11.0", page)

    def test_the_homepage_has_no_link_without_a_release(self):
        with mock.patch("base.views.release_highlights", return_value=[]):
            page = self.client.get(reverse("base:home")).content.decode()
        self.assertNotIn("What's new in version", page)
