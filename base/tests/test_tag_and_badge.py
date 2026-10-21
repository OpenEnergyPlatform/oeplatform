"""One tag and status badges (#2645), as a browser receives them.

A Tag used to be drawn six ways: a `btn` with an inline background (factsheet
detail and list, the tag overview, the table page), a dot inside a light badge
(the table list) and a checkbox label (the factsheet editor's picker), most of
them with the text colour computed inline beside it. Now every one goes
through `components/tag.html`, which asks `readable_text_color` -- the one
place that decides contrast -- and writes both colours as custom properties.
Statuses are a separate `badge`, never a pill; "Early Access" is an info badge
rather than a red one that reads like an error.

The tables tab's chips are not here: they move with the dashboard lists
(#2659).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.urls import reverse
from django.utils import timezone

from base.tests import TestViewsTestCase
from dataedit.models import Dataset, Table, Tag
from dataedit.tests.test_dataset_sidebar import SidebarFixture
from modelview.tests.corpus import seed_corpus
from modelview.tests.html import element_markup

TAG_INCLUDE = "components/tag.html"

#: A dark colour, so `readable_text_color` answers white.
DARK = "#4A148C"
#: A light one, so it answers black.
LIGHT = "#F9E79F"


def render_tag(**context):
    return " ".join(render_to_string(TAG_INCLUDE, context).split())


def tag_links(html):
    """Every link variant on the page, as its opening tag."""
    return re.findall(r'<a class="tag tag--link"[^>]*>', html)


class TagIncludeTest(SimpleTestCase):
    """The include's four variants, rendered on their own."""

    def test_static_is_a_span_in_the_tags_own_colour(self):
        markup = render_tag(name="Wind", color=DARK)

        self.assertTrue(markup.startswith('<span class="tag"'))
        self.assertIn(f"--tag-color: {DARK}", markup)
        self.assertIn(">Wind</span>", markup)

    def test_the_text_colour_comes_from_the_contrast_helper(self):
        self.assertIn("--tag-text-color: #FFFFFF", render_tag(name="a", color=DARK))
        self.assertIn("--tag-text-color: #000000", render_tag(name="a", color=LIGHT))

    def test_no_variant_paints_an_inline_background(self):
        for variant in (
            {},
            {"href": "?tags=wind"},
            {"remove": "wind"},
            {"toggle_name": "tags", "toggle_value": "wind"},
        ):
            with self.subTest(variant=variant):
                markup = render_tag(name="Wind", color=DARK, **variant)
                self.assertNotIn("background", markup)
                self.assertNotIn("btn", markup)

    def test_a_tag_without_a_colour_is_neutral(self):
        """A topic, say: no colour, so no style at all; the neutral surface
        is the stylesheet's fallback."""
        self.assertNotIn("style=", render_tag(name="energy"))

    def test_link(self):
        markup = render_tag(
            name="Wind",
            color=DARK,
            href="/factsheets/models/?tags=wind",
            title="Filter by Wind",
        )

        self.assertTrue(markup.startswith('<a class="tag tag--link"'))
        self.assertIn('href="/factsheets/models/?tags=wind"', markup)
        self.assertIn('title="Filter by Wind"', markup)
        self.assertNotIn("hx-get", markup)

    def test_link_loaded_in_place(self):
        markup = render_tag(
            name="Wind", href="/e", hx_get="/e", hx_target="#m", hx_swap="outerHTML"
        )

        for attribute in ('hx-get="/e"', 'hx-target="#m"', 'hx-swap="outerHTML"'):
            self.assertIn(attribute, markup)

    def test_removable_has_a_labelled_close_button(self):
        markup = render_tag(name="Wind", color=DARK, remove="wind")

        self.assertIn('class="tag tag--removable"', markup)
        self.assertRegex(
            markup,
            r'<button type="button" class="tag__remove" data-tag-remove="wind"'
            r' aria-label="Remove Wind">',
        )

    def test_toggle_is_a_label_around_its_checkbox(self):
        markup = render_tag(
            name="Wind",
            color=DARK,
            toggle_name="tags",
            toggle_value="wind",
            toggle_id="select_wind",
            checked=True,
        )

        self.assertTrue(markup.startswith('<label class="tag tag--toggle"'))
        self.assertRegex(
            markup,
            r'<input type="checkbox" class="tag__check" name="tags" value="wind"'
            r' id="select_wind" checked />',
        )
        self.assertNotIn(" checked", render_tag(name="a", toggle_name="t"))

    def test_a_name_is_escaped(self):
        self.assertIn("&lt;b&gt;", render_tag(name="<b>"))


class EveryTagGoesThroughTheIncludeTest(SimpleTestCase):
    """A scan of every template, so a seventh rendering cannot creep back."""

    def templates(self):
        return [
            path
            for path in Path(settings.BASE_DIR).glob("*/templates/**/*.html")
            if "node_modules" not in path.parts
        ]

    def test_only_the_include_asks_for_a_tags_text_colour(self):
        include = Path(settings.BASE_DIR) / "base" / "templates" / TAG_INCLUDE
        askers = [
            str(path.relative_to(settings.BASE_DIR))
            for path in self.templates()
            if "readable_text_color" in path.read_text(encoding="utf-8")
            and path != include
        ]
        self.assertEqual(askers, [])

    def test_no_tag_is_a_button_and_no_status_is_a_legacy_class(self):
        legacy = re.compile(r"\bbtn tag\b|\bearly-access\b|\bsuccess-badge\b")
        offenders = [
            str(path.relative_to(settings.BASE_DIR))
            for path in self.templates()
            if legacy.search(path.read_text(encoding="utf-8"))
        ]
        self.assertEqual(offenders, [])


class FactsheetTagsTest(TestViewsTestCase):
    def setUp(self):
        self.corpus = seed_corpus(sheettype="model", factsheets=1, corrupted=0)
        self.sheet = self.corpus.factsheets[0]
        self.tag = Tag.objects.create(
            name="Tag Component Wind", color=int("2E7D32", 16)
        )
        self.sheet.tags.add(self.tag)

    def test_the_detail_page_links_each_tag_to_the_filtered_list(self):
        html = self.get(
            "modelview:show-factsheet",
            kwargs={"sheettype": "model", "pk": self.sheet.pk},
        ).content.decode()

        expected = (
            reverse("modelview:modellist", args=["model"]) + "?tags=" + self.tag.pk
        )
        self.assertIn(f'href="{expected}"', " ".join(tag_links(html)))
        self.assertNotIn('href=""', html)

    def test_the_list_filters_with_toggles_and_draws_its_column_from_the_include(self):
        html = self.get(
            "modelview:modellist", kwargs={"sheettype": "model"}
        ).content.decode()

        self.assertIn('class="tag tag--toggle"', html)
        template = element_markup(html, "factsheet-tag-template")
        self.assertIn('class="tag tag--link"', template)


class TagOverviewTest(TestViewsTestCase):
    def test_each_tag_opens_its_editor_in_place(self):
        tag = Tag.objects.create(name="Tag Component Solar", color=int("F9A825", 16))

        html = self.get("dataedit:tags", logged_in=True).content.decode()

        edit = reverse("dataedit:tags-edit", args=[tag.pk])
        link = next(link for link in tag_links(html) if f'href="{edit}"' in link)
        self.assertIn(f'hx-get="{edit}"', link)
        self.assertIn('hx-target="#tag-manager"', link)


class TableListTagsTest(TestViewsTestCase):
    def setUp(self):
        self.table = Table.objects.create(
            name="tag_component_listed", is_sandbox=False, is_publish=False
        )
        self.tag = Tag.objects.create(
            name="Tag Component Heat", color=int("6A1B9A", 16)
        )
        self.table.tags.add(self.tag)

    def tearDown(self):
        self.table.delete()

    def test_a_tag_filters_the_topic_it_is_listed_in(self):
        html = self.get(
            "dataedit:tables-in-topic", kwargs={"topic": settings.PSEUDO_TOPIC_DRAFT}
        ).content.decode()

        topic = reverse(
            "dataedit:tables-in-topic", kwargs={"topic": settings.PSEUDO_TOPIC_DRAFT}
        )
        self.assertIn(
            f'href="{topic}?query=&amp;tags={self.tag.pk}"', " ".join(tag_links(html))
        )
        self.assertNotIn("tag-badge", html)


class TablePageTest(SidebarFixture):
    def test_the_tables_tags_link_to_the_filtered_tables(self):
        tag = Tag.objects.create(name="Tag Component Grid", color=int("00838F", 16))
        self.table.tags.add(tag)

        html = self.client.get(self.view_url).content.decode()

        topics = reverse("dataedit:topic-list")
        self.assertIn(
            f'href="{topics}?query=&amp;tags={tag.pk}"', " ".join(tag_links(html))
        )

    def test_early_access_is_an_info_badge(self):
        html = self.client.get(self.view_url).content.decode()

        self.assertRegex(html, r'<span class="badge badge--info">\s*Early Access')

    def test_a_draft_dataset_carries_a_warning_badge(self):
        # A draft is shown to its creator only.
        self.make_dataset("tag_component_draft", published=False)
        self.client.force_login(self.user)

        html = self.client.get(self.view_url).content.decode()

        self.assertIn('class="badge badge--warning ms-1"', html)


class DatasetDetailBadgeTest(SidebarFixture):
    def test_a_published_member_carries_a_success_badge(self):
        Table.objects.filter(pk=self.table.pk).update(is_publish=True)
        dataset = Dataset.objects.create(
            name="tag_component_ds",
            metadata={"name": "tag_component_ds", "title": "T", "description": ""},
            creator=self.user,
            published_at=timezone.now(),
        )
        dataset.tables.add(self.table)

        html = self.client.get(
            reverse("dataedit:dataset-detail", kwargs={"dataset_name": dataset.name})
        ).content.decode()

        self.assertRegex(html, r'<span class="badge badge--success[^"]*">Published')
