"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The component catalogue at /styleguide/ (#2636), through the test client, and
what ``manage.py check_catalogue`` refuses.

The check itself runs in the catalogue workflow, not here: a house component
without an entry should fail the catalogue's own status, not the test suite.
So these tests run the check against small trees of their own, to show what it
refuses and what it accepts, and never against the repository's.
"""  # noqa: 501

import html
import io
import re
import shutil
import tempfile
from pathlib import Path
from unittest import mock

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.urls import reverse

from base import styleguide
from base.styleguide import TOKENS, Token, catalogue_problems, entry_files, split_entry
from modelview.tests.html import element_markup, text

STYLEGUIDE = reverse("base:styleguide")


class CatalogueTest(TestCase):
    def page(self, query=""):
        response = self.client.get(STYLEGUIDE + query)
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_answers_anonymously_in_both_token_modes(self):
        for query in ("", "?tokens=theme", "?tokens=bootstrap"):
            with self.subTest(query=query):
                self.page(query)

    def test_is_not_indexed(self):
        self.assertRegex(self.page(), r'<meta name="robots" content="noindex"\s*/?>')

    def test_is_linked_from_no_menu(self):
        # The navbar and the footer of a page that is not the catalogue.
        page = self.client.get(reverse("base:about")).content.decode()
        self.assertNotIn(f'href="{STYLEGUIDE}', page)

    def test_has_one_h1(self):
        self.assertEqual(len(re.findall(r"<h1\b", self.page())), 1)

    def test_renders_every_entry_and_shows_its_source(self):
        page = self.page()
        self.assertTrue(entry_files(), "the catalogue has no entry")
        for name, path in entry_files().items():
            with self.subTest(entry=name):
                note, source = split_entry(path.read_text())
                section = element_markup(page, name)
                self.assertIn(note, html.unescape(text(section)))
                shown = element_markup(page, f"{name}-source")
                # The source as it is in the file, escaped, not rendered.
                self.assertEqual(html.unescape(text(shown)), " ".join(source.split()))
                self.assertIn('data-copy="%s-source"' % name, section)

    def test_lists_every_token_in_the_table(self):
        page = self.page()
        for token in TOKENS:
            with self.subTest(token=token.name):
                self.assertIn(f'data-token="{token.name}"', page)
                self.assertIn(f'style="--sample: var({token.name})"', page)

    def test_only_the_bootstrap_mode_loads_the_stock_tokens(self):
        self.assertNotIn("stock_tokens.css", self.page())
        self.assertNotIn("stock_tokens.css", self.page("?tokens=nonsense"))
        stock = self.page("?tokens=bootstrap")
        # The last stylesheet, after the theme, so its :root wins.
        head = stock[: stock.index("</head>")]
        sheets = re.findall(r'<link\b[^>]*rel="stylesheet"[^>]*href="([^"]*)"', head)
        self.assertTrue(sheets[-1].endswith("stock_tokens.css"), sheets)

    def test_marks_the_current_token_mode(self):
        for mode, label in styleguide.TOKEN_MODES.items():
            with self.subTest(mode=mode):
                page = self.page(f"?tokens={mode}")
                current = re.findall(
                    r'<a [^>]*aria-current="page"[^>]*>([^<]*)</a>', page
                )
                self.assertEqual([c.strip() for c in current], [label])

    def test_every_button_on_the_page_carries_a_role(self):
        # The page's own; the navbar's toggler is the shell's.
        main = element_markup(self.page(), "main-content")
        for button in re.findall(r"<button\b[^>]*>", main):
            with self.subTest(button=button):
                self.assertRegex(button, r'class="[^"]*\bbtn\b[^"]*\bbtn-link\b')


class LinkWithArrowTest(TestCase):
    """The homepage's onward links are the house link_with_arrow."""

    def test_homepage_feature_links_are_house_components(self):
        page = self.client.get(reverse("base:home")).content.decode()
        links = re.findall(r'<a class="([^"]*\bindex-feature-link\b[^"]*)"', page)
        self.assertTrue(links)
        for classes in links:
            self.assertIn("link-with-arrow", classes.split())
        self.assertNotIn("index-feature-link-arrow", page)
        self.assertIn("link-with-arrow__icon", page)


class CheckCatalogueTest(TestCase):
    """What check_catalogue refuses, on trees of its own."""

    THEME = ":root{--bs-primary: #1F567D;--oep-measure: 70ch}"
    STOCK = ":root{--bs-primary: #0d6efd;--oep-measure: none}"
    TOKENS = (
        Token("--bs-primary", "colour", "x"),
        Token("--oep-measure", "width", "x"),
    )

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        for name in ("partials", "includes", "entries"):
            (self.root / name).mkdir()
        self.write("theme.css", self.THEME)
        self.write("stock.css", self.STOCK)

    def write(self, name, content):
        path = self.root / name
        path.write_text(content)
        return path

    def problems(self, tokens=None):
        return catalogue_problems(
            partials=self.root / "partials",
            includes=self.root / "includes",
            entries=self.root / "entries",
            theme=self.root / "theme.css",
            stock=self.root / "stock.css",
            tokens=self.TOKENS if tokens is None else tokens,
        )

    def test_a_complete_tree_passes(self):
        self.write("partials/_button.scss", "")
        self.write("includes/alert.html", "")
        self.write("entries/button.html", "{# use: the main action #}\n<b>x</b>\n")
        self.write("entries/alert.html", "{# use: a message #}\n<i>x</i>\n")
        self.write("entries/_helper.html", "no note needed")
        self.assertEqual(self.problems(), [])

    def test_a_partial_without_an_entry_fails(self):
        self.write("partials/_button.scss", "")
        (problem,) = self.problems()
        self.assertIn("button", problem)
        self.assertIn("entries/button.html", problem)

    def test_an_include_without_an_entry_fails(self):
        self.write("includes/confirm_dialog.html", "")
        (problem,) = self.problems()
        self.assertIn("confirm_dialog", problem)

    def test_a_helper_is_not_an_entry(self):
        self.write("partials/_button.scss", "")
        self.write("entries/_button.html", "{# use: x #}\n")
        self.assertEqual(len(self.problems()), 1)

    def test_an_entry_without_its_note_fails(self):
        self.write("entries/button.html", "<b>x</b>\n")
        (problem,) = self.problems()
        self.assertIn("{# use: ... #}", problem)

    def test_a_token_the_table_does_not_list_fails(self):
        self.write("theme.css", self.THEME[:-1] + ";--oep-new: 1px}")
        (problem,) = self.problems()
        self.assertIn("--oep-new", problem)

    def test_a_listed_token_without_a_stock_value_fails(self):
        self.write("stock.css", ":root{--bs-primary: #0d6efd}")
        (problem,) = self.problems()
        self.assertIn("--oep-measure", problem)
        self.assertIn("stock", problem)

    def test_the_command_fails_with_the_problems_and_passes_without(self):
        self.write("partials/_button.scss", "")
        with mock.patch(
            "base.management.commands.check_catalogue.catalogue_problems",
            self.problems,
        ):
            with self.assertRaisesRegex(CommandError, "button"):
                call_command("check_catalogue", stdout=io.StringIO())
            self.write("entries/button.html", "{# use: x #}\n")
            # The rendering half asks the real page in both token modes.
            out = io.StringIO()
            call_command("check_catalogue", stdout=out)
            self.assertIn("complete", out.getvalue())
