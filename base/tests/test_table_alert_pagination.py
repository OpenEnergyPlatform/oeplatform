"""Tables, alerts and pagination (#2647), as a browser receives them.

A table used to be a bare grid, a `profiletable`, DataTables' stock `display`
or a `.table` with rounded corners on the table itself (which collapsed
borders ignore). Now every touched table is Bootstrap's `.table` (`.table-pairs`
for labels and values), its corners come from the one `.table-container`
wrapper, and DataTables draws it through its Bootstrap 5 styling. A message
was an `alert-variant`, an inline red div or Bootstrap's stock alert; now it is
the house alert, written by `components/alert.html`. The two list pagers are
Bootstrap's `.pagination` without their shadow and small size.

What is checked is what a page carries -- classes, roles, which stylesheet and
script a page loads -- never how the theme draws it.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from pathlib import Path

from django.conf import settings
from django.contrib.messages import constants
from django.contrib.messages.storage.base import Message
from django.template.loader import render_to_string
from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from base.tests import TestViewsTestCase
from dataedit.models import Table
from dataedit.tests.test_dataset_sidebar import SidebarFixture
from dataedit.views import ITEMS_PER_PAGE
from login.models import ADMIN_PERM, WRITE_PERM, Membership, Organization
from login.tests.helpers import HTMX, act_as, make_user
from modelview.tests.corpus import seed_corpus

ALERT_INCLUDE = "components/alert.html"
BASE_DIR = Path(settings.BASE_DIR)


def squash(markup):
    return " ".join(markup.split())


def render_alert(**context):
    return squash(render_to_string(ALERT_INCLUDE, context))


class AlertIncludeTest(SimpleTestCase):
    def test_each_status_is_bootstraps_status_class(self):
        for status in ("success", "info", "warning", "danger"):
            with self.subTest(status=status):
                self.assertIn(
                    f'class="alert alert-{status}"',
                    render_alert(status=status, text="x"),
                )

    def test_without_a_status_it_is_information(self):
        self.assertIn('class="alert alert-info"', render_alert(text="x"))

    def test_a_warning_or_an_error_is_announced_and_the_rest_waits(self):
        for status, role in (
            ("danger", "alert"),
            ("warning", "alert"),
            ("success", "status"),
            ("info", "status"),
        ):
            with self.subTest(status=status):
                self.assertIn(f'role="{role}"', render_alert(status=status, text="x"))

    def test_the_icon_is_the_stylesheets_not_the_markup(self):
        """So an alert a script writes gets it too."""
        markup = render_alert(status="success", text="Saved")
        self.assertNotIn("<i ", markup)
        self.assertNotIn("<svg", markup)

    def test_dismissible_has_a_labelled_close_button(self):
        markup = render_alert(status="info", text="x", dismissible=True)

        self.assertIn("alert-dismissible fade show", markup)
        self.assertIn(
            'class="btn-close" data-bs-dismiss="alert" aria-label="Close"', markup
        )
        self.assertNotIn("btn-close", render_alert(status="info", text="x"))

    def test_text_is_escaped(self):
        self.assertIn("&lt;b&gt;", render_alert(text="<b>"))

    def test_an_id_for_a_script_or_a_target(self):
        self.assertIn('id="upload-error"', render_alert(text="x", id="upload-error"))
        self.assertNotIn("id=", render_alert(text="x"))


class MessagesRegionTest(SimpleTestCase):
    """Every Django message renders as the house alert."""

    def render(self, *messages):
        return squash(render_to_string("base/messages.html", {"messages": messages}))

    def test_each_level_is_its_status(self):
        markup = self.render(
            Message(constants.SUCCESS, "Saved"),
            Message(constants.INFO, "Note"),
            Message(constants.WARNING, "Careful"),
            Message(constants.ERROR, "Failed"),
        )

        for status, text in (
            ("success", "Saved"),
            ("info", "Note"),
            ("warning", "Careful"),
            ("danger", "Failed"),
        ):
            self.assertRegex(
                markup,
                rf'class="alert alert-{status} alert-dismissible fade show"'
                rf' role="\w+"> {text} <button',
            )

    def test_extra_tags_do_not_pick_another_look(self):
        """An extra tag used to land in the class list (`alert-primary info`)."""
        markup = self.render(Message(constants.INFO, "Created", extra_tags="primary"))

        self.assertIn('class="alert alert-info alert-dismissible', markup)
        self.assertNotIn("primary", markup)


class LegacyVariantsAreGoneTest(SimpleTestCase):
    """A scan, so a superseded variant cannot creep back."""

    def sources(self, *patterns):
        for pattern in patterns:
            for path in BASE_DIR.glob(pattern):
                vendored = {"node_modules", "vendor"} & set(path.parts)
                if not vendored and not path.name.endswith(".min.js"):
                    yield path

    def offenders(self, regex, *patterns):
        return [
            str(path.relative_to(BASE_DIR))
            for path in self.sources(*patterns)
            if regex.search(path.read_text(encoding="utf-8"))
        ]

    def test_no_template_or_script_uses_a_superseded_variant(self):
        legacy = re.compile(
            r"\bprofiletable\b|\balert-variant|<table[^>]*class=\"display\""
            r"|style=\"[^\"]*color: ?red|jquery\.dataTables\.min\.css"
        )
        self.assertEqual(
            self.offenders(
                legacy,
                "*/templates/**/*.html",
                "*/static/**/*.js",
                "*/templatetags/*.py",
            ),
            [],
        )

    def test_the_theme_rounds_no_bare_table(self):
        """A radius on `table` itself does nothing on collapsed borders; the
        `.table-container` wrapper rounds a table."""
        bare_table_radius = re.compile(
            r"^\s*table\s*\{[^}]*border-radius", re.MULTILINE
        )
        self.assertEqual(
            self.offenders(bare_table_radius, "theming/scss/**/*.scss"), []
        )


class DataTablesPagesTest(SidebarFixture):
    """Both DataTables pages load its Bootstrap 5 styling and the house
    defaults, in that order after the core, and draw a house table."""

    def assert_bootstrap5_datatables(self, html):
        scripts = [
            "dataedit/jquery.dataTables.min.js",
            "dataedit/dataTables.bootstrap5.min.js",
            "dataedit/datatables_house.js",
        ]
        positions = [html.find(script) for script in scripts]
        self.assertNotIn(-1, positions, scripts)
        self.assertEqual(positions, sorted(positions))
        self.assertIn("dataedit/dataTables.bootstrap5.min.css", html)
        self.assertNotIn("jquery.dataTables.min.css", html)

    # The table page loads its scripts in a compress block; uncompressed, the
    # page names the files themselves.
    @override_settings(COMPRESS_ENABLED=False)
    def test_the_table_page(self):
        html = self.client.get(self.view_url).content.decode()

        self.assert_bootstrap5_datatables(html)
        self.assertIn('<table class="table table-hover" id="datatable"', html)

    def test_the_factsheet_list(self):
        seed_corpus(sheettype="model", factsheets=1, corrupted=0)
        html = self.client.get(
            reverse("modelview:modellist", kwargs={"sheettype": "model"})
        ).content.decode()

        self.assert_bootstrap5_datatables(html)
        self.assertIn('<table id="overview" class="table table-hover"', html)


class TablePageReviewTabTest(SidebarFixture):
    def test_its_notices_are_house_alerts(self):
        html = squash(self.client.get(self.view_url).content.decode())

        # The fixture's table has no metadata, so a review is not possible.
        self.assertIn(
            '<div class="alert alert-warning" role="alert"> No metadata available.',
            html,
        )
        self.assertNotIn("alert-variant", html)


class FactsheetDetailTest(TestViewsTestCase):
    def test_both_kinds_list_their_fields_in_house_tables(self):
        for sheettype in ("model", "framework"):
            with self.subTest(sheettype=sheettype):
                sheet = seed_corpus(
                    sheettype=sheettype, factsheets=1, corrupted=0
                ).factsheets[0]

                html = self.get(
                    "modelview:show-factsheet",
                    kwargs={"sheettype": sheettype, "pk": sheet.pk},
                ).content.decode()

                self.assertIn('<table class="table table-pairs">', html)
                self.assertNotIn("profiletable", html)


class OrganizationErrorsTest(TestViewsTestCase):
    """The two inline red errors on the organization page."""

    def setUp(self):
        self.admin = make_user("AlertOrgAdmin")
        self.organization = Organization.objects.create(name="alert_org")
        Membership.objects.create(
            user=self.admin, group=self.organization, level=ADMIN_PERM
        )
        act_as(self.client, self.admin)

    def test_a_refused_leave_answers_a_house_alert(self):
        response = self.client.post(
            reverse(
                "login:organization-leave",
                kwargs={"organization_id": self.organization.pk},
            ),
            **HTMX,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            '<div class="alert alert-danger" role="alert"> Please delete the'
            " organization instead",
            squash(response.content.decode()),
        )

    def test_an_unknown_invitee_is_a_house_alert(self):
        Membership.objects.filter(group=self.organization).update(level=WRITE_PERM)
        response = self.client.post(
            reverse(
                "login:partial-organization-membership",
                kwargs={"organization_id": self.organization.pk},
            ),
            {"mode": "add_user", "name": "nobody_by_this_name"},
            **HTMX,
        )

        html = squash(response.content.decode())
        self.assertIn(
            '<div class="alert alert-danger" role="alert"> User does not exist', html
        )
        self.assertNotIn("color: red", html)


class ListPagerTest(TestViewsTestCase):
    """The table list's two pagers, on a list of two pages."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Table.objects.bulk_create(
            Table(name=f"pager_test_{n:03}", is_sandbox=False, is_publish=False)
            for n in range(ITEMS_PER_PAGE + 1)
        )

    def test_the_table_list(self):
        html = self.get(
            "dataedit:tables-in-topic", kwargs={"topic": settings.PSEUDO_TOPIC_DRAFT}
        ).content.decode()

        self.assertEqual(html.count('<ul class="pagination'), 2)
        self.assertNotIn("pagination-sm", html)
        self.assertNotRegex(html, r'class="page-link[^"]*shadow')
        self.assertEqual(html.count('class="page-item active" aria-current="page"'), 2)
