"""
The dashboard's list tabs on the house components (#2659, spec #2632): Topics
as tags, statuses as badges, the row menu as the house dropdown behind a
button with a role, the pager as the house pagination, and the messages in
the shell's one toast region rather than one of the list's own. Read through
HTTP, by structure and classes only.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dataedit.models import Dataset, Table, Topic
from login.listing import PAGE_SIZE
from login.models import ADMIN_PERM, UserPermission
from login.tests.helpers import make_user
from modelview.tests.html import element_markup

#: A static tag (components/tag.html) and its name.
TAG = re.compile(r'<span class="tag"\s*>([^<]*)</span>')


def classes(markup):
    """The classes of the first element in ``markup``."""
    found = re.search(r'\bclass="([^"]*)"', markup)
    return set(found.group(1).split()) if found else set()


class ListTabTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("HouseListOwner")
        cls.topics = [
            Topic.objects.get_or_create(name=name)[0]
            for name in ("house_a", "house_b", "house_c")
        ]

    def setUp(self):
        self.client.force_login(self.user)

    def page(self, tab):
        response = self.client.get(
            reverse(f"login:{tab}", kwargs={"user_id": self.user.pk})
        )
        self.assertEqual(response.status_code, 200)
        return response.content.decode()


class TablesTabTests(ListTabTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # one page and one more, so the pager shows
        for number in range(PAGE_SIZE + 1):
            table = Table.objects.create(
                name=f"house_{number:02d}", is_publish=number == 0
            )
            UserPermission.objects.create(
                holder=cls.user, table=table, level=ADMIN_PERM
            )
            if number == 0:
                table.topics.set(cls.topics)
                cls.published = table

    def test_topics_are_tags_and_the_rest_behind_a_link_button(self):
        html = self.page("tables")
        row = element_markup(html, f"row-{self.published.pk}")
        popover = element_markup(html, f"tp-{self.published.pk}-pop")
        self.assertNotIn("dash-tchip", html)
        self.assertIn('class="tag-group"', row)
        # two in the cell, all three in its popover
        cell = row.replace(popover, "")
        self.assertEqual(TAG.findall(cell), ["house_a", "house_b"])
        self.assertEqual(TAG.findall(popover), ["house_a", "house_b", "house_c"])
        more = element_markup(html, f"tp-{self.published.pk}")
        self.assertTrue({"btn", "btn-link"} <= classes(more))

    def test_statuses_are_house_badges(self):
        html = self.page("tables")
        self.assertNotIn("dash-badge", html)
        self.assertIn('class="badge badge--success">Published', html)
        self.assertIn('class="badge badge--warning">Draft', html)

    def test_the_cells_that_act_carry_a_role(self):
        html = self.page("tables")
        pk = self.published.pk
        for cell in (f"pub-{pk}", f"acc-{pk}", f"menu-{pk}"):
            with self.subTest(cell=cell):
                self.assertTrue(
                    {"btn", "btn-link"} <= classes(element_markup(html, cell))
                )

    def test_the_row_menu_is_the_house_dropdown(self):
        html = self.page("tables")
        delete = element_markup(html, f"menu-{self.published.pk}-delete")
        self.assertTrue({"dropdown-item", "text-danger"} <= classes(delete))
        self.assertNotIn("dash-menu__list", html)

    def test_the_pager_is_the_house_pagination(self):
        html = self.page("tables")
        self.assertIn('<ul class="pagination', html)
        self.assertIn('<li class="page-item active" aria-current="page">', html)
        self.assertEqual(classes(element_markup(html, "pg-2")), {"page-link"})
        self.assertIn('<li class="pagination__range">', html)

    def test_messages_go_to_the_shells_one_toast_region(self):
        html = self.page("tables")
        self.assertEqual(html.count('id="toasts-polite"'), 1)
        self.assertEqual(html.count('id="toasts-assertive"'), 1)
        self.assertIn('id="toast-template"', html)
        self.assertNotIn("dash-toasts", html)


class DatasetsTabTests(ListTabTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.draft = Dataset.objects.create(
            name="house_draft",
            metadata={"name": "house_draft", "title": "Draft", "description": ""},
            creator=cls.user,
        )
        cls.draft.topics.set(cls.topics[:1])
        cls.published = Dataset.objects.create(
            name="house_published",
            metadata={"name": "house_published", "title": "Pub", "description": ""},
            creator=cls.user,
            published_at=timezone.now(),
        )

    def test_topics_are_tags_and_statuses_badges(self):
        html = self.page("datasets")
        self.assertNotIn("dash-tchip", html)
        self.assertNotIn("dash-badge", html)
        row = element_markup(html, f"row-{self.draft.pk}")
        self.assertEqual(TAG.findall(row), ["house_a"])
        self.assertIn('class="badge badge--warning">Draft', row)
        self.assertIn(
            'class="badge badge--success">Published',
            element_markup(html, f"row-{self.published.pk}"),
        )

    def test_the_row_menu_toggle_carries_a_role(self):
        html = self.page("datasets")
        toggle = element_markup(html, f"menu-{self.draft.pk}")
        self.assertTrue({"btn", "btn-link"} <= classes(toggle))

    def test_messages_go_to_the_shells_one_toast_region(self):
        html = self.page("datasets")
        self.assertEqual(html.count('id="toasts-polite"'), 1)
        self.assertNotIn("dash-toasts", html)
