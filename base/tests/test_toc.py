"""The "On this page" list (toc) and the two pages that carry it first, about
and the privacy policy (#2649, spec #2632, WF-13's chosen layouts).

Asserted here, as a browser receives the pages:

- the include alone: a navigation landmark named by its visible label "On this
  page", the entries in an ordered list;
- on each page: the list opens a .toc-layout whose body holds the text, and
  its entries are the page's own h2s, in order, word for word, each linking to
  its heading;
- about: the research projects and partners are sibling h2 sections, each
  project is listed once, the logos carry no inline sizes or margin hacks;
- privacy: the rights are listed one entry per article, the controller is an
  <address>, the cookie table is the house table.

The texts themselves are checked against their snapshots in
test_page_header.py. Structure only, never CSS; the horizontal overflow at
390 px is measured in a browser and shown in the pull request.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from pathlib import Path

from django.template.loader import render_to_string
from django.test import SimpleTestCase

from base.tests import TestViewsTestCase
from base.tests.html_tree import parse

PROJECTS = Path(__file__).parents[1] / "static" / "project_detail_pages_content"


class ComponentTest(SimpleTestCase):
    def test_a_labelled_list_of_the_entries(self):
        root = parse(
            render_to_string(
                "components/toc.html",
                {"entries": "styleguide/entries/_toc_entries.html"},
            )
        )
        nav = root.find("nav", "toc")
        label = root.find(css_class="toc__title")
        self.assertEqual(label.text(), "On this page")
        self.assertEqual(nav.attrs["aria-labelledby"], label.attrs["id"])
        links = nav.find("ol", "toc__list").find_all("a")
        self.assertEqual(
            [a.attrs["href"] for a in links],
            ["#toc-example-first", "#toc-example-second"],
        )


class PageTest(TestViewsTestCase):
    def page(self, view):
        return parse(self.get(view, expect_status=200).content.decode())

    def layout(self, root):
        layout = root.find(css_class="toc-layout")
        toc, body = layout.elements
        self.assertTrue(toc.has_class("toc"))
        self.assertTrue(body.has_class("toc-layout__body"))
        return toc, body

    def assertEntriesAreTheHeadings(self, root, count):
        toc, body = self.layout(root)
        entries = [(a.attrs["href"], a.text()) for a in toc.find_all("a")]
        headings = [
            ("#" + h.attrs.get("id", ""), h.text()) for h in body.find_all("h2")
        ]
        self.assertEqual(entries, headings)
        self.assertEqual(len(entries), count)
        self.assertEqual(len(root.find_all("nav", "toc")), 1)


class AboutTest(PageTest):
    def setUp(self):
        self.root = self.page("base:about")

    def test_the_toc_lists_the_seven_sections(self):
        self.assertEntriesAreTheHeadings(self.root, 7)

    def test_projects_and_partners_are_sibling_sections(self):
        _toc, body = self.layout(self.root)
        sections = [h.text() for h in body.elements if h.tag == "h2"]
        self.assertEqual(
            sections[-3:], ["Supported By", "Research Projects", "Partners"]
        )
        self.assertEqual(body.find_all("h3") + body.find_all("h4"), [])

    def test_each_project_is_listed_once(self):
        # The files beside their hashed copies in STATIC_ROOT listed every
        # project twice once static names carried a content hash (#2604).
        grid = self.root.find("ul", "logo-grid--projects")
        tiles = grid.find_all("a", "logo-tile")
        expected = sorted(p.stem for p in PROJECTS.glob("*.json"))
        found = sorted(a.attrs["href"].rstrip("/").rsplit("/", 1)[-1] for a in tiles)
        self.assertEqual(found, expected)

    def test_logos_carry_no_inline_sizes(self):
        _toc, body = self.layout(self.root)
        for node in body.iter():
            with self.subTest(tag=node.tag, attrs=node.attrs):
                self.assertFalse(
                    {"style", "width", "height", "border"} & set(node.attrs)
                )
        grids = body.find_all("ul", "logo-grid")
        self.assertEqual(len(grids), 3)
        for img in body.find_all("img"):
            self.assertTrue(img.attrs.get("alt"))


class PrivacyPolicyTest(PageTest):
    def setUp(self):
        self.root = self.page("base:legal-privacy-policy")

    def test_the_toc_lists_the_eight_sections(self):
        self.assertEntriesAreTheHeadings(self.root, 8)

    def test_rights_are_one_entry_per_article(self):
        _toc, body = self.layout(self.root)
        articles = [dt.text() for dt in body.find_all("dt")]
        self.assertEqual(
            [a.split(" GDPR")[0] for a in articles],
            ["Art. 15", "Art. 16", "Art. 17", "Art. 18", "Art. 20", "Art. 77"]
            + ["Art. 21", "Art. 7 par. 3"],
        )
        self.assertEqual(len(body.find_all("dd")), len(articles))

    def test_the_controller_is_an_address(self):
        address = self.root.find("address")
        self.assertIn("Till Mossakowski", address.text())
        self.assertIsNotNone(address.find("a"))

    def test_the_cookie_table_is_the_house_table(self):
        table = self.root.find("table")
        self.assertTrue(table.has_class("table"))
        self.assertTrue(table.parent.has_class("table-container"))
        self.assertNotIn("style", table.attrs)
        self.assertEqual(len(table.find("thead").find_all("th")), 4)
        self.assertEqual(len(table.find("tbody").find_all("tr")), 2)
