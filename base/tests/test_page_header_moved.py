"""The pages that had a ``main-header`` or a legacy ``h2.site-header`` carry
the house page header instead (#2640, spec #2632).

The old header named the area in the page's ``h1`` ("Database", "Ontology")
and the subject in a trail under it; the band names the area on a line of its
own and makes the subject the trail's last part and the page's one ``h1``.
Asserted here, as a browser receives each page:

- exactly one ``h1``, inside the band, as the trail's last, current item;
- the area, the trail's links and the subject each row of ``MOVED`` names;
- the band sits inside ``main``, above the content;
- the page's text outside the band is the text it had outside its old header
  before this ticket, word for word (``page_texts/moved_*.txt``, captured from
  the unchanged templates): what sat in the old header besides its area and
  trail (an introduction, a sentence on how to use the page) moved into the
  page, not away. A status the old header showed as a badge ("You can edit
  this table.") is the band's description now, asserted per row. Runs of
  tags are left out on both sides: they come in no fixed order.

The React apps' insides are out of scope (spec #2632): the ontology search and
entity apps still draw a heading of their own in the browser, after the server
sends the page this test reads.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from pathlib import Path
from typing import NamedTuple

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse

from base.tests.html_tree import parse
from base.tests.test_page_lint import NOT_TEMPLATES, Page, PageFixture
from dataedit.models import PeerReview, PeerReviewManager

BAND = "page-header"
AREA = "page-header__area"
TRAIL = "page-header__trail"
DESCRIPTION = "page-header__description"
SNAPSHOTS = Path(__file__).parent / "page_texts"

DRAFT = settings.PSEUDO_TOPIC_DRAFT
TABLE = {"table": "{table}"}
TOPICS = ("Topics", "dataedit:topic-list", {})
TABLE_LINK = ("{table}", "dataedit:view", TABLE)
TAGS = ("Tags", "dataedit:tags", {})
ONTOLOGY_OVERVIEW = ("Overview", "ontology:index", {})


def overview(sheettype):
    return ("Overview", "modelview:modellist", {"sheettype": sheettype})


class Moved(NamedTuple):
    page: Page
    area: str
    # The trail's links as (label, view, kwargs), in order; the title follows.
    # Labels, titles and kwargs may name the fixture's things ("{table}").
    links: tuple
    title: str
    description: str | None = None


MOVED = {
    # Database
    "topics": Moved(Page("dataedit:topic-list"), "Database", (), "Topics"),
    "tables_in_topic": Moved(
        Page("dataedit:tables-in-topic", {"topic": DRAFT}), "Database", (TOPICS,), DRAFT
    ),
    "datasets_in_topic": Moved(
        Page("dataedit:datasets-in-topic", {"topic": DRAFT}),
        "Database",
        (TOPICS, (DRAFT, "dataedit:tables-in-topic", {"topic": DRAFT})),
        "Datasets",
    ),
    "dataset_detail": Moved(
        Page("dataedit:dataset-detail", {"dataset_name": "{dataset}"}),
        "Database",
        (TOPICS,),
        "T",
    ),
    "table": Moved(
        Page("dataedit:view", TABLE, logged_in=True),
        "Database",
        (TOPICS,),
        "{table}",
        description="You can edit this table.",
    ),
    "table_permissions": Moved(
        Page("dataedit:table-permission", TABLE, logged_in=True),
        "Database",
        (TOPICS, TABLE_LINK),
        "Permissions",
    ),
    "meta_edit": Moved(
        Page("dataedit:meta_edit", TABLE, logged_in=True),
        "Database",
        (TOPICS, TABLE_LINK),
        "Edit Metadata",
        description="You can edit the metadata.",
    ),
    "oemetabuilder": Moved(
        Page("dataedit:oemetabuilder"),
        "Metadata",
        (),
        "Edit Metadata",
        description="Standalone (no data table attached)",
    ),
    "table_graph": Moved(
        Page("dataedit:table-graph", TABLE, logged_in=True),
        "Database",
        (TOPICS, TABLE_LINK),
        "Create Graph View",
    ),
    "table_map": Moved(
        Page("dataedit:table-map", {**TABLE, "maptype": "latlon"}, logged_in=True),
        "Database",
        (TOPICS, TABLE_LINK),
        "Create Map View",
    ),
    "tags": Moved(Page("dataedit:tags", logged_in=True), "Database", (), "Tags"),
    "tag_new": Moved(
        Page("dataedit:tags-new", logged_in=True), "Database", (TAGS,), "Create Tag"
    ),
    "tag_edit": Moved(
        Page("dataedit:tags-edit", {"tag_pk": "{tag}"}, logged_in=True),
        "Database",
        (TAGS,),
        "Edit Tag",
    ),
    "wizard_create": Moved(
        Page("dataedit:wizard_create", logged_in=True), "Database", (), "Create table"
    ),
    "wizard_upload": Moved(
        Page("dataedit:wizard_upload", TABLE, logged_in=True),
        "Database",
        (TOPICS, TABLE_LINK),
        "Upload data from csv",
    ),
    "peer_review": Moved(
        Page("dataedit:peer_review_create", TABLE, logged_in=True),
        "Database",
        (TOPICS, TABLE_LINK),
        "Review",
    ),
    "peer_review_contributor": Moved(
        Page(
            "dataedit:peer_review_contributor",
            {**TABLE, "review_id": "{review}"},
            logged_in=True,
        ),
        "Database",
        (TOPICS, TABLE_LINK),
        "Review",
    ),
    # Factsheets: the spec's worked row (area "Model Factsheets", trail
    # "Overview / name (acronym)"), and the same form on every factsheet page.
    "model_list": Moved(
        Page("modelview:modellist", {"sheettype": "model"}),
        "Model Factsheets",
        (),
        "Overview",
    ),
    "framework_list": Moved(
        Page("modelview:modellist", {"sheettype": "framework"}),
        "Framework Factsheets",
        (),
        "Overview",
    ),
    "model": Moved(
        Page(
            "modelview:show-factsheet",
            {"sheettype": "model", "pk": "{model}"},
            logged_in=True,
        ),
        "Model Factsheets",
        (overview("model"),),
        "{model_subject}",
    ),
    "framework": Moved(
        Page(
            "modelview:show-factsheet",
            {"sheettype": "framework", "pk": "{framework}"},
            logged_in=True,
        ),
        "Framework Factsheets",
        (overview("framework"),),
        "{framework_subject}",
    ),
    "model_edit": Moved(
        Page("modelview:edit", {"sheettype": "model", "pk": "{model}"}, logged_in=True),
        "Model Factsheets",
        (
            overview("model"),
            (
                "{model_name}",
                "modelview:show-factsheet",
                {"sheettype": "model", "pk": "{model}"},
            ),
        ),
        "Edit",
    ),
    "model_add": Moved(
        Page("modelview:modeladd", {"sheettype": "model"}, logged_in=True),
        "Model Factsheets",
        (overview("model"),),
        "New model factsheet",
    ),
    "framework_edit": Moved(
        Page(
            "modelview:edit",
            {"sheettype": "framework", "pk": "{framework}"},
            logged_in=True,
        ),
        "Framework Factsheets",
        (
            overview("framework"),
            (
                "{framework_name}",
                "modelview:show-factsheet",
                {"sheettype": "framework", "pk": "{framework}"},
            ),
        ),
        "Edit",
    ),
    "framework_add": Moved(
        Page("modelview:modeladd", {"sheettype": "framework"}, logged_in=True),
        "Framework Factsheets",
        (overview("framework"),),
        "New framework factsheet",
    ),
    # Ontology, and the knowledge graph's query page under Scenario Bundles
    "ontology": Moved(Page("ontology:index"), "Ontology", (), "Overview"),
    "oeo_steering_committee": Moved(
        Page("ontology:oeo-s-c"),
        "Ontology",
        (ONTOLOGY_OVERVIEW,),
        "Steering Committee (OEO-SC)",
    ),
    "oeo_search": Moved(
        Page("ontology:ontology-entity-search", {"ontology": "oeo"}),
        "Ontology",
        (ONTOLOGY_OVERVIEW,),
        "OEO Search",
    ),
    "oeo_entity": Moved(
        Page(
            "ontology:oeo-class-detail", {"ontology": "oeo", "term_id": "BFO_0000001"}
        ),
        "Ontology",
        (
            ONTOLOGY_OVERVIEW,
            ("OEO Search", "ontology:ontology-entity-search", {"ontology": "oeo"}),
        ),
        "Entity",
    ),
    "oeo_viewer": Moved(
        Page("oeo_viewer:index"),
        "Ontology",
        (ONTOLOGY_OVERVIEW,),
        "Open Energy Ontology Viewer",
    ),
    "oekg": Moved(
        Page("oekg:main", logged_in=True), "Scenario Bundles", (), "OEKG Sparql Query"
    ),
    # The catalogue: the spec's worked row
    "styleguide": Moved(
        Page("base:styleguide"), "Styleguide", (), "Component catalogue"
    ),
}

#: Areas that are not a navbar menu: the spec's worked rows name them.
AREAS_OFF_THE_NAVBAR = {"Model Factsheets", "Framework Factsheets", "Styleguide"}


def subject(sheet):
    return (
        f"{sheet.model_name} ({sheet.acronym})" if sheet.acronym else sheet.model_name
    )


class MovedPagesTest(PageFixture):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.review = PeerReview.objects.create(
            table=cls.table.name, reviewer=cls.user, review={}
        )
        PeerReviewManager.objects.create(opr=cls.review)

    @classmethod
    def tearDownClass(cls):
        cls.review.delete()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.names.update(
            review=self.review.pk,
            model_name=self.model.model_name,
            framework_name=self.framework.model_name,
            model_subject=subject(self.model),
            framework_subject=subject(self.framework),
        )

    def fill(self, value):
        return value.format(**self.names) if isinstance(value, str) else value

    def root(self, slug):
        return parse(self.html(MOVED[slug].page))

    def band(self, root):
        """The page's own band: the catalogue shows more inside its content."""
        bands = [
            band
            for band in root.find_all("header", BAND)
            if not any(a.has_class("content") for a in band.ancestors)
        ]
        self.assertEqual(len(bands), 1, "one band")
        return bands[0]

    def test_exactly_one_h1_inside_the_band_as_the_trails_last_part(self):
        for slug in MOVED:
            with self.subTest(page=slug):
                root = self.root(slug)
                band = self.band(root)
                h1s = root.find_all("h1")
                self.assertEqual(len(h1s), 1, "one h1")
                items = band.find("ol", TRAIL).elements
                self.assertIs(h1s[0].parent, items[-1])
                self.assertEqual(items[-1].attrs.get("aria-current"), "page")

    def test_area_trail_subject_and_description(self):
        for slug, moved in MOVED.items():
            with self.subTest(page=slug):
                root = self.root(slug)
                band = self.band(root)
                self.assertEqual(band.find(css_class=AREA).text(), moved.area)
                found = [
                    (a.text(), a.attrs["href"])
                    for a in band.find("ol", TRAIL).find_all("a")
                ]
                expected = [
                    (
                        self.fill(label),
                        reverse(
                            view,
                            kwargs={k: self.fill(v) for k, v in kwargs.items()},
                        ),
                    )
                    for label, view, kwargs in moved.links
                ]
                self.assertEqual(found, expected)
                self.assertLessEqual(len(found), 2, "at most two link levels")
                self.assertEqual(root.find("h1").text(), self.fill(moved.title))
                description = band.find(css_class=DESCRIPTION)
                self.assertEqual(description and description.text(), moved.description)

    def test_areas_are_the_navbars_labels(self):
        # No new wording: an area is one of the navbar's menus, unless the
        # spec's worked rows name it.
        for slug, moved in MOVED.items():
            if moved.area in AREAS_OFF_THE_NAVBAR:
                continue
            with self.subTest(page=slug):
                root = self.root(slug)
                menus = {a.text() for a in root.find("nav", "navbar").find_all("a")}
                self.assertIn(moved.area, menus)

    def test_the_band_sits_inside_main_above_the_content(self):
        for slug in MOVED:
            with self.subTest(page=slug):
                root = self.root(slug)
                main = root.find("main")
                band = self.band(root)
                self.assertIn(main, band.ancestors)
                content = root.find(css_class="content")
                if content is not None:  # the React shell has none
                    order = list(main.iter())
                    self.assertLess(order.index(band), order.index(content))

    def test_no_page_keeps_an_old_header(self):
        for slug in MOVED:
            with self.subTest(page=slug):
                root = self.root(slug)
                self.assertIsNone(root.find(css_class="main-header"))
                self.assertIsNone(root.find(css_class="site-header"))

    def test_texts_outside_the_band_are_unchanged(self):
        for slug in MOVED:
            with self.subTest(page=slug):
                root = self.root(slug)
                band = self.band(root)
                text = root.find("main").text(
                    skip=lambda node: node is band or unordered(node)
                )
                before = (SNAPSHOTS / f"moved_{slug}.txt").read_text().strip()
                self.assertEqual(normalised(text), before)


class NoOldHeaderTest(SimpleTestCase):
    """Neither old header comes back: no template or theme source names one."""

    # The class, not the shells' `site-header` block that holds the band.
    OLD = re.compile(r'main-header|class="[^"]*\bsite-header\b|\.site-header\b')

    def test_no_source_uses_an_old_header(self):
        root = Path(settings.BASE_DIR)
        offenders = []
        for pattern in ("*.html", "*.scss", "*.css"):
            for path in sorted(root.rglob(pattern)):
                relative = path.relative_to(root).as_posix()
                if any(part in "/" + relative for part in NOT_TEMPLATES):
                    continue
                for line in path.read_text("utf-8").splitlines():
                    if self.OLD.search(line):
                        offenders.append(f"{relative}: {line.strip()}")
        self.assertEqual(offenders, [])


def unordered(node):
    # A run of tags comes in no fixed order; this ticket does not touch it.
    return node.has_class("tag-group")


def normalised(text):
    # Values the fixture makes anew on every run (primary keys, the corpus's
    # numbered names, dates) are not words the templates write.
    return re.sub(r"\d+", "#", text)
