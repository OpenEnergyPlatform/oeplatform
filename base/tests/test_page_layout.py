"""The page layout (#2638, spec #2632): an opt-in side column and plain
section headings, as a browser receives the pages.

The side column used to be in every shell, so a page with nothing to put in it
still sat beside an empty 21rem column. Now a shell renders none unless the
page fills its `side-column` block, and the main column takes the width left
over. Three things are asserted: pages without side content render no side
column; every page that had side content still shows it, in the shell's place
for it; and no template fills a block its shell no longer has, which is how
side content would vanish without an error.

Assertions are on structure (which columns exist, in which order, what they
hold, which headings carry which classes), never on CSS. The widths and the
typography are checked outside the suite, by eye and by the homepage
comparison (benchmarks/homepage/compare.mjs).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from pathlib import Path

from django.conf import settings
from django.template import engines
from django.template.loader_tags import BlockNode, ExtendsNode
from django.test import SimpleTestCase

from dataedit.tests.test_dataset_sidebar import SidebarFixture
from modelview.tests.corpus import seed_corpus
from modelview.tests.html import elements_with_class

MAIN = "content__main"
SIDE = "content__side"


class SideColumnTestCase(SidebarFixture):
    """The pages, with one table, one dataset and one factsheet of each kind
    behind them."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.factsheets = {
            sheettype: seed_corpus(sheettype=sheettype, factsheets=1, corrupted=0)
            .factsheets[0]
            .pk
            for sheettype in ("model", "framework")
        }

    def setUp(self):
        super().setUp()
        self.make_dataset("layout_dataset")

    def columns(self, view_name, kwargs=None, logged_in=False):
        """(main column, side columns) of a page, as markup."""
        html = self.get(view_name, kwargs=kwargs, logged_in=logged_in).content
        return self.split(html.decode())

    def split(self, html):
        mains = elements_with_class(html, MAIN)
        self.assertEqual(len(mains), 1, "one main column")
        return mains[0], elements_with_class(html, SIDE)


class PagesWithoutSideContentTest(SideColumnTestCase):
    PAGES = (
        ("base:contact", None),
        ("base:legal-privacy-policy", None),
        ("base:legal-tou", None),
        ("base:faq", None),
        ("base:discussion", None),
        ("base:oefamily-sc", None),
        ("base:project_detail", {"project_id": "open_ego"}),
    )

    def test_render_no_side_column(self):
        for view_name, kwargs in self.PAGES:
            with self.subTest(page=view_name):
                _main, sides = self.columns(view_name, kwargs)
                self.assertEqual(sides, [])

    def test_the_tag_overview_renders_no_side_column(self):
        _main, sides = self.columns("dataedit:tags", logged_in=True)
        self.assertEqual(sides, [])

    def test_a_missing_page_renders_no_side_column(self):
        response = self.client.get("/no/such/page/")
        self.assertEqual(response.status_code, 404)
        _main, sides = self.split(response.content.decode())
        self.assertEqual(sides, [])

    def test_factsheet_edit_pages_render_no_side_column(self):
        for sheettype, pk in self.factsheets.items():
            with self.subTest(sheettype=sheettype):
                _main, sides = self.columns(
                    "modelview:edit",
                    {"sheettype": sheettype, "pk": pk},
                    logged_in=True,
                )
                self.assertEqual(sides, [])


class PagesWithSideContentTest(SideColumnTestCase):
    """Every page that filled the old side block, each with something only
    its side content says."""

    def assertSide(self, view_name, kwargs, says, logged_in=False, left=False):
        html = self.get(view_name, kwargs=kwargs, logged_in=logged_in).content
        html = html.decode()
        main, sides = self.split(html)
        self.assertEqual(len(sides), 1, "one side column")
        self.assertIn(says, sides[0])
        self.assertNotIn(says, main)
        # The profile shell has its column on the left, every other on the right.
        self.assertEqual(self.opens(html, SIDE) < self.opens(html, MAIN), left)

    def opens(self, html, css_class):
        """Where the first element carrying `css_class` starts."""
        return re.search(r'class="(?:[^"]*\s)?%s[\s"]' % css_class, html).start()

    def test_factsheet_detail(self):
        for sheettype, pk in self.factsheets.items():
            with self.subTest(sheettype=sheettype):
                self.assertSide(
                    "modelview:show-factsheet",
                    {"sheettype": sheettype, "pk": pk},
                    says="Actions",
                )

    def test_factsheet_list(self):
        self.assertSide("modelview:modellist", {"sheettype": "model"}, says="Tags")

    def test_table_view(self):
        self.assertSide("dataedit:view", {"table": self.table_name}, says="Datasets")

    def test_table_permissions(self):
        self.assertSide(
            "dataedit:table-permission",
            {"table": self.table_name},
            says="This page shows the users",
            logged_in=True,
        )

    def test_dataset_detail(self):
        self.assertSide(
            "dataedit:dataset-detail",
            {"dataset_name": "layout_dataset"},
            says="Resources",
        )

    def test_catalogue(self):
        self.assertSide("base:styleguide", None, says="On this page")

    def test_ontology(self):
        # Filled by htmx once the page has loaded.
        self.assertSide("ontology:index", None, says='id="content-sidebar"')

    def test_profile_pages_have_it_on_the_left(self):
        for view_name in (
            "login:datasets",
            "login:tables",
            "login:reviews",
            "login:organizations",
            "login:settings",
        ):
            with self.subTest(page=view_name):
                self.assertSide(
                    view_name,
                    {"user_id": self.user.pk},
                    says="Member since",
                    logged_in=True,
                    left=True,
                )


class SectionHeadingTest(SideColumnTestCase):
    """section_heading is a plain h2 or h3: the profile pages' section
    headings lost their classes, and the theme's heading rules style them."""

    CLASSED = re.compile(
        # the class itself, not one that ends in it (card-header, site-header)
        r"<h[1-6]\b[^>]*\bclass=\"(?:[^\"]*\s)?(header|profile-category__heading)[\s\"]"
    )

    def test_profile_section_headings_carry_no_class(self):
        for view_name, heading in (
            ("login:settings", "<h2>Your Security Information</h2>"),
            ("login:reviews", "<h2>Active Open Peer Reviews</h2>"),
            ("login:organizations", "<h3>Memberships</h3>"),
        ):
            with self.subTest(page=view_name):
                html = self.get(
                    view_name, kwargs={"user_id": self.user.pk}, logged_in=True
                ).content.decode()
                self.assertIn(heading, html)
                self.assertIsNone(self.CLASSED.search(html))


def _blocks(nodelist):
    """Every block in a node list, at any depth."""
    found = set()
    for node in nodelist:
        if isinstance(node, BlockNode):
            found.add(node.name)
        for attr in node.child_nodelists:
            found |= _blocks(getattr(node, attr, None) or [])
    return found


class BlockChainTest(SimpleTestCase):
    """A child template's block that no ancestor defines is dropped without a
    word. Moving the side column into its own block made every old side
    block such a block, so this holds the move to account for all of them,
    and any later rename of a shell's blocks too."""

    def templates(self):
        engine = engines["django"].engine
        root = Path(settings.BASE_DIR)
        for loader in engine.template_loaders:
            for directory in map(Path, loader.get_dirs()):
                if (
                    not directory.is_relative_to(root)
                    or "site-packages" in directory.parts  # a venv in the checkout
                    or not directory.exists()
                ):
                    continue  # a package's templates, not this repository's
                for path in directory.rglob("*.html"):
                    yield engine, str(path.relative_to(directory))

    def chain(self, engine, name):
        """(the blocks a template fills at its top level, every block its
        ancestors define); None for the second if it extends nothing."""
        nodes = engine.get_template(name).nodelist
        extends = next((n for n in nodes if isinstance(n, ExtendsNode)), None)
        if extends is None or not isinstance(extends.parent_name.var, str):
            return _blocks(nodes), None
        filled = {n.name for n in extends.nodelist if isinstance(n, BlockNode)}
        defined, parent = set(), extends.parent_name.var.strip("'\"")
        while parent:
            nodes = engine.get_template(parent).nodelist
            parent_extends = next(
                (n for n in nodes if isinstance(n, ExtendsNode)), None
            )
            defined |= _blocks(parent_extends.nodelist if parent_extends else nodes)
            parent = (
                parent_extends.parent_name.var.strip("'\"")
                if parent_extends and isinstance(parent_extends.parent_name.var, str)
                else None
            )
        return filled, defined

    def test_every_block_a_template_fills_exists_up_its_chain(self):
        checked = 0
        for engine, name in self.templates():
            filled, defined = self.chain(engine, name)
            if defined is None:
                continue
            checked += 1
            with self.subTest(template=name):
                self.assertEqual(filled - defined, set())
        self.assertGreater(checked, 50, "the templates were not found")
