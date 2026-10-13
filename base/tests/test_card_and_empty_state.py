"""Cards and empty states (#2646), as a browser receives them.

A card used to be built three ways: the theme's card mixins (`topic-card`,
`organization-card`, and `profile-table-card`, which no template used any
more), and raw Bootstrap cards with utilities beside them (the dataset and
table lists, the dataset page). Now every card is Bootstrap's `.card`, which
the theme turns into the house card on tokens; a card that leads to one page
is `card--clickable`, its title link stretched over it.

An empty list used to say so four ways: a plain paragraph (the dataset
list), an info alert (the table list), the dashboard's `.dash-empty`, and
nothing at all (the organizations tab). Now each goes through
`components/empty_state.html`: a muted icon, one sentence, at most one
action. The table permissions page's empty texts are not here: they move with
that page (#2657).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from dataedit.models import Dataset, Table, Topic
from login.models import Membership, Organization
from login.permissions import ADMIN_PERM
from login.tests.helpers import HTMX, make_user
from modelview.tests.html import elements_with_class, text
from oeplatform.settings import PSEUDO_TOPIC_DRAFT

EMPTY_STATE = "components/empty_state.html"


def render_empty_state(**context):
    return render_to_string(EMPTY_STATE, context)


def empty_states(html):
    return elements_with_class(html, "empty-state")


def actions(markup):
    """The buttons and links an empty state offers, as opening tags: every
    element carrying `btn`, and every link."""
    return [
        tag
        for tag in re.findall(r"<(?:a|button)\b[^>]*>", markup)
        if tag.startswith("<a") or re.search(r'class="[^"]*\bbtn\b', tag)
    ]


def classes_of(markup):
    found = re.match(r'\s*<[a-z]+\b[^>]*\bclass="([^"]*)"', markup)
    return found.group(1).split() if found else []


class EmptyStateIncludeTest(SimpleTestCase):
    """The include on its own."""

    def test_says_its_sentence_beside_a_hidden_icon(self):
        markup = render_empty_state(text="Nothing here yet.", icon="fas fa-table")

        self.assertEqual(text(markup), "Nothing here yet.")
        self.assertRegex(
            markup,
            r'<span class="empty-state__icon fas fa-table"\s+aria-hidden="true">',
        )

    def test_has_a_default_icon(self):
        self.assertIn("fas fa-inbox", render_empty_state(text="x"))

    def test_the_title_and_the_action_are_optional(self):
        bare = render_empty_state(text="x")
        self.assertNotIn("empty-state__title", bare)
        self.assertNotIn("empty-state__action", bare)

        full = render_empty_state(
            text="x",
            title="You have no datasets yet",
            action_template="styleguide/entries/_empty_state_action.html",
        )
        self.assertIn(
            '<p class="empty-state__title">You have no datasets yet</p>', full
        )
        self.assertEqual(len(actions(full)), 1)

    def test_a_sentence_with_markup_comes_from_its_own_template(self):
        markup = render_empty_state(
            text_template="login/partials/tables_empty_text.html",
            EXTERNAL_URLS=settings.EXTERNAL_URLS,
        )
        self.assertIn('id="empty-api"', markup)
        self.assertIn("appear here", text(markup))

    def test_an_image_takes_the_icons_place_above_the_title(self):
        markup = render_empty_state(
            text="x", title="Lost", image="/static/p.png", image_alt="OEPlatypus"
        )

        self.assertNotIn("empty-state__icon", markup)
        self.assertIn(
            '<img class="empty-state__image" src="/static/p.png" alt="OEPlatypus" />',
            markup,
        )
        self.assertLess(markup.index("<img"), markup.index("Lost"))

    def test_heading_makes_the_title_the_pages_h1(self):
        self.assertIn(
            '<h1 class="empty-state__title empty-state__title--page">Lost</h1>',
            render_empty_state(text="x", title="Lost", heading=True),
        )
        self.assertNotIn("<h1", render_empty_state(text="x", title="Lost"))

    def test_an_example_heading_has_the_look_without_the_h1(self):
        # The catalogue shows it inside a page with its own h1.
        markup = render_empty_state(
            text="x", title="Lost", heading=True, as_example=True
        )
        self.assertNotIn("<h1", markup)
        self.assertIn(
            '<p class="empty-state__title empty-state__title--page">Lost</p>', markup
        )

    def test_compact_is_a_modifier(self):
        self.assertEqual(
            classes_of(render_empty_state(text="x", compact=True)),
            ["empty-state", "empty-state--compact"],
        )
        self.assertEqual(classes_of(render_empty_state(text="x")), ["empty-state"])


class TemplateScanTest(SimpleTestCase):
    """Nothing builds a card or an empty state the old ways any more."""

    RETIRED = (
        "topic-card__tag",
        "topic-card__header",
        "organization-card__tag",
        "organization-card__btn",
        "organization-management",
        "profile-table-card",
        "dash-empty",
        "profile-category__no_organization_table",
    )

    def templates(self):
        root = Path(settings.BASE_DIR)
        for path in root.glob("*/templates/**/*.html"):
            yield path, path.read_text(encoding="utf-8")

    def test_no_template_uses_a_retired_class(self):
        for path, source in self.templates():
            for retired in self.RETIRED:
                with self.subTest(template=str(path), retired=retired):
                    self.assertNotIn(retired, source)

    def test_only_the_include_writes_an_empty_state(self):
        for path, source in self.templates():
            if path.as_posix().endswith(EMPTY_STATE):
                continue
            with self.subTest(template=str(path)):
                self.assertNotRegex(source, r'class="empty-state\b')

    def test_no_card_drops_the_house_border_or_shadow(self):
        """A `.card` that switched off its border or shadow with utilities
        would be a card of its own again."""
        for path, source in self.templates():
            for opening in re.findall(r'<[a-z]+\b[^>]*class="card\b[^"]*"', source):
                with self.subTest(template=str(path), card=opening):
                    self.assertNotRegex(opening, r"\b(border-0|shadow-sm|shadow)\b")

    def test_the_theme_has_no_card_or_empty_state_mixin(self):
        scss = Path(settings.BASE_DIR) / "theming"
        for path in scss.rglob("*.scss"):
            source = path.read_text(encoding="utf-8")
            with self.subTest(partial=str(path)):
                self.assertNotRegex(
                    source,
                    r"@mixin (cards-layout|card-container|card-simple-container"
                    r"|empty-state|tag-mark)\b",
                )


class TopicListTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Topic.objects.get_or_create(name="supply")
        table = Table.objects.create(name="tt_supply_table", is_publish=True)
        table.topics.add("supply")
        Table.objects.create(name="tt_draft_table")

    def page(self):
        response = self.client.get(reverse("dataedit:topic-list"))
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def cards(self):
        return elements_with_class(self.page(), "topic-card")

    def test_every_topic_is_a_clickable_house_card(self):
        cards = self.cards()
        self.assertEqual(len(cards), 2)
        for card in cards:
            with self.subTest(card=text(card)[:30]):
                self.assertEqual(
                    classes_of(card)[:3], ["card", "card--clickable", "topic-card"]
                )
                self.assertNotIn("onclick", card)

    def test_the_title_link_opens_the_topic_and_stretches_over_the_card(self):
        card = next(c for c in self.cards() if "supply" in text(c))
        link = re.search(r'<a class="stretched-link"\s+href="([^"]*)">supply</a>', card)
        self.assertIsNotNone(link, card)
        self.assertEqual(
            link.group(1),
            reverse("dataedit:tables-in-topic", kwargs={"topic": "supply"}),
        )

    def test_a_card_has_a_header_above_its_body(self):
        # The header holds the title, the count and the keywords; the body
        # holds the description (and the draft's wizard).
        # From the page, not from a card's markup: re-parsing that markup
        # closes the header early at the icon's self-closing <path />.
        page = self.page()
        header = next(
            h for h in elements_with_class(page, "card-header") if "supply" in text(h)
        )
        body = elements_with_class(page, "topic-card__body")[-1]  # supply comes last

        self.assertIn("supply", text(header))
        self.assertIn("tables", text(header))
        self.assertIn("commodity", text(header))
        self.assertNotIn("commodity", text(body))

    def test_the_draft_card_is_wide_and_a_topic_card_is_not(self):
        draft = next(c for c in self.cards() if PSEUDO_TOPIC_DRAFT in text(c))
        supply = next(c for c in self.cards() if "supply" in text(c))

        self.assertIn("topic-card--wide", classes_of(draft))
        self.assertNotIn("topic-card--wide", classes_of(supply))

    def test_the_keywords_are_neutral_tags(self):
        card = next(c for c in self.cards() if "supply" in text(c))
        self.assertRegex(card, r'<span class="tag"\s*>commodity</span>')
        self.assertNotIn("--tag-color", card)

    def test_the_draft_card_offers_the_wizard_above_its_link(self):
        card = next(c for c in self.cards() if PSEUDO_TOPIC_DRAFT in text(c))
        wizard = re.search(
            r'<a class="([^"]*card__control[^"]*)"\s+href="([^"]*)">', card
        )
        self.assertEqual(wizard.group(2), reverse("dataedit:wizard_create"))
        self.assertIn("card__control", wizard.group(1).split())
        self.assertIn("btn-primary", wizard.group(1).split())


class DatasetPagesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("CardsDatasetOwner")
        cls.topic, _ = Topic.objects.get_or_create(name="energy")

    def dataset(self, name, tables=()):
        dataset = Dataset.objects.create(
            name=name,
            metadata={"title": f"Title of {name}"},
            creator=self.user,
            published_at=timezone.now(),
        )
        dataset.topics.add(self.topic)
        for table in tables:
            dataset.tables.add(Table.objects.create(name=table, is_publish=True))
        return dataset

    def get(self, name, **kwargs):
        response = self.client.get(reverse(name, kwargs=kwargs))
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_a_dataset_in_the_list_is_a_clickable_card(self):
        self.dataset("cards_ds")
        page = self.get("dataedit:datasets-in-topic", topic="energy")
        cards = elements_with_class(page, "card--clickable")
        self.assertEqual(len(cards), 1)
        self.assertIn("stretched-link", cards[0])
        self.assertIn(
            reverse("dataedit:dataset-detail", kwargs={"dataset_name": "cards_ds"}),
            cards[0],
        )

    def test_an_empty_dataset_list_is_an_empty_state(self):
        page = self.get("dataedit:datasets-in-topic", topic="energy")
        (empty,) = empty_states(page)
        self.assertEqual(text(empty), "No datasets have been published yet.")
        self.assertEqual(actions(empty), [])

    def test_the_draft_topic_explains_in_an_empty_state(self):
        page = self.get("dataedit:datasets-in-topic", topic=PSEUDO_TOPIC_DRAFT)
        (empty,) = empty_states(page)
        self.assertIn("Datasets are not listed under the draft topic.", text(empty))

    def test_an_empty_table_list_is_an_empty_state(self):
        page = self.get("dataedit:tables-in-topic", topic="energy")
        (empty,) = empty_states(page)
        self.assertEqual(
            text(empty), "No tables found in this topic matching your filters."
        )
        self.assertNotIn("alert-info", page)

    def test_a_table_in_the_list_is_a_house_card(self):
        table = Table.objects.create(name="cards_listed_table", is_publish=True)
        table.topics.add(self.topic)
        page = self.get("dataedit:tables-in-topic", topic="energy")
        (card,) = [c for c in elements_with_class(page, "card") if table.name in c]
        # `resource-card` is not a style any more but the hook tablelist.js
        # fills each card's metadata and size through.
        self.assertEqual(classes_of(card), ["card", "resource-card", "w-100"])
        self.assertIn("metadata-injection-zone", card)

    def test_a_dataset_without_tables_says_so_compactly(self):
        self.dataset("cards_empty_ds")
        page = self.get("dataedit:dataset-detail", dataset_name="cards_empty_ds")
        (empty,) = empty_states(page)
        self.assertIn("empty-state--compact", classes_of(empty))
        self.assertEqual(text(empty), "No tables assigned yet.")

    def test_the_dataset_page_uses_house_cards(self):
        self.dataset("cards_full_ds", tables=("cards_member",))
        page = self.get("dataedit:dataset-detail", dataset_name="cards_full_ds")
        self.assertGreaterEqual(len(elements_with_class(page, "card")), 3)
        self.assertEqual(empty_states(page), [])


class OrganizationsTabTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("CardsOrgMember")

    def setUp(self):
        self.client.force_login(self.user)

    def page(self):
        response = self.client.get(
            reverse("login:organizations", kwargs={"user_id": self.user.pk})
        )
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def join(self, name, level):
        organization = Organization.objects.create(name=name, description="About it")
        Membership.objects.create(user=self.user, group=organization, level=level)
        return organization

    def test_a_membership_is_a_house_card_with_a_role_badge(self):
        self.join("cards_org_admin", ADMIN_PERM)
        self.join("cards_org_member", 4)
        cards = elements_with_class(self.page(), "organization-card")
        self.assertEqual(len(cards), 2)
        by_name = {text(card).split()[0]: card for card in cards}
        self.assertEqual(classes_of(by_name["cards_org_admin"])[:1], ["card"])
        self.assertIn(
            '<span class="badge badge--info">Admin</span>', by_name["cards_org_admin"]
        )
        self.assertIn(
            '<span class="badge badge--neutral">Member</span>',
            by_name["cards_org_member"],
        )

    def test_edit_carries_a_role(self):
        self.join("cards_org_edit", ADMIN_PERM)
        (card,) = elements_with_class(self.page(), "organization-card")
        (edit,) = re.findall(r"<button\b[^>]*>", card)
        self.assertRegex(edit, r'class="btn btn-secondary btn-sm"')

    def test_no_membership_is_an_empty_state_without_an_action(self):
        (empty,) = empty_states(self.page())
        self.assertEqual(text(empty), "You are not a member of any organization yet.")
        self.assertEqual(actions(empty), [])

    def test_an_organization_without_tables_says_so(self):
        organization = self.join("cards_org_tables", ADMIN_PERM)
        response = self.client.get(
            reverse(
                "login:organization-edit",
                kwargs={"organization_id": organization.group_ptr_id},
            ),
            **HTMX,
        )
        self.assertEqual(response.status_code, 200)
        (empty,) = empty_states(response.content.decode())
        self.assertEqual(text(empty), "No tables are assigned to this organization.")


class DashboardEmptyStatesTest(TestCase):
    """The tables and datasets tabs: empty, and nothing matching."""

    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("CardsDashboardOwner")

    def setUp(self):
        self.client.force_login(self.user)

    def page(self, name, query=None):
        response = self.client.get(
            reverse(name, kwargs={"user_id": self.user.pk}), query or {}
        )
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_no_tables_offers_the_wizard_and_points_at_the_api(self):
        (empty,) = empty_states(self.page("login:tables"))
        self.assertIn("You have no tables yet", text(empty))
        (wizard,) = [a for a in actions(empty) if "btn" in a]
        self.assertIn('id="empty-create"', wizard)
        self.assertIn(reverse("dataedit:wizard_create"), wizard)
        api = re.search(r'<a id="empty-api"\s+href="([^"]*)"', empty)
        self.assertEqual(api.group(1), settings.EXTERNAL_URLS["tutorials_api_upload"])

    def test_no_datasets_offers_one_action(self):
        (empty,) = empty_states(self.page("login:datasets"))
        self.assertIn("You have no datasets yet", text(empty))
        (create,) = actions(empty)
        self.assertIn('id="datasets-create"', create)

    def test_nothing_matching_offers_reset(self):
        Dataset.objects.create(name="cards_dash_ds", metadata={}, creator=self.user)
        (empty,) = empty_states(self.page("login:datasets", {"search": "nothing"}))
        self.assertEqual(text(empty), "No datasets match these filters. Reset filters")
        (reset,) = actions(empty)
        self.assertIn('id="nomatch-reset"', reset)
