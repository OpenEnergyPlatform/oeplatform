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
  <address>, the cookie table is the house table;
- terms of use (#2650): both languages in the page, each a section opening
  with its own heading, the "English | Deutsch" switch above the list and
  hidden until language_switch.js reveals it (so without JavaScript nothing
  is hidden), the list's entries tagged with their language.

What the switch does in a browser is tested with vitest
(base/static/base/__tests__/language_switch.test.js).

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


class TermsOfUseTest(PageTest):
    def setUp(self):
        self.root = self.page("base:legal-tou")
        layout = self.root.find(css_class="toc-layout")
        self.side, self.body = layout.elements

    def sections(self):
        return [s for s in self.body.elements if s.tag == "section"]

    def test_the_switch_sits_above_the_list(self):
        self.assertTrue(self.side.has_class("toc-layout__side"))
        self.assertTrue(self.body.has_class("toc-layout__body"))
        switch, toc = self.side.elements
        self.assertTrue(toc.has_class("toc"))
        self.assertEqual(switch.attrs.get("role"), "radiogroup")
        self.assertTrue(switch.attrs.get("aria-label"))
        radios = switch.find_all("input")
        self.assertEqual([r.attrs["value"] for r in radios], ["en", "de"])
        self.assertEqual({r.attrs["type"] for r in radios}, {"radio"})
        self.assertEqual({r.attrs["name"] for r in radios}, {"language"})
        self.assertIn("checked", radios[0].attrs)
        labels = switch.find_all("label")
        self.assertEqual([la.text() for la in labels], ["English", "Deutsch"])
        self.assertEqual(
            [la.attrs["for"] for la in labels], [r.attrs["id"] for r in radios]
        )
        self.assertEqual([la.attrs["lang"] for la in labels], ["en", "de"])

    def test_without_javascript_only_the_switch_is_hidden(self):
        # The module hides one language; the page itself hides nothing a
        # reader without JavaScript would need, and no switch that does
        # nothing without it.
        hidden = [n for n in self.root.find("main").iter() if "hidden" in n.attrs]
        self.assertEqual(hidden, [self.root.find(css_class="btn-group")])
        self.assertIn("data-language-switch", hidden[0].attrs)

    def test_each_language_is_a_section_opening_with_its_heading(self):
        sections = self.sections()
        self.assertEqual(
            [
                (s.attrs["id"], s.attrs["lang"], s.attrs["data-language"])
                for s in sections
            ],
            [("en", "en", "en"), ("de", "de", "de")],
        )
        self.assertEqual(
            [s.elements[0].text() for s in sections],
            ["Terms of Use", "Nutzungsbedingungen"],
        )
        self.assertEqual([s.elements[0].tag for s in sections], ["h2", "h2"])

    def test_the_toc_lists_each_languages_headings_tagged_with_it(self):
        toc = self.side.find("nav", "toc")
        entries = [
            (li.attrs["data-language"], li.find("a").attrs["href"], li.text())
            for li in toc.find_all("li")
        ]
        headings = [
            (s.attrs["data-language"], "#" + h.attrs["id"], h.text())
            for s in self.sections()
            for h in s.find_all("h3")
        ]
        self.assertEqual(entries, headings)
        self.assertEqual(len(entries), 4)
        self.assertEqual(len(self.root.find_all("nav", "toc")), 1)

    def test_no_text_points_down_to_the_translation(self):
        text = self.root.find("main").text()
        for gone in ("down below", "weiter unten", "\U0001f1ec", "\U0001f1e9"):
            self.assertNotIn(gone, text)

    def test_the_page_binds_the_switch(self):
        scripts = [
            s.text()
            for s in self.root.find_all("script")
            if s.attrs.get("type") == "module"
        ]
        self.assertTrue(
            any(
                "language_switch.js" in s and "bindLanguageSwitch" in s for s in scripts
            )
        )
