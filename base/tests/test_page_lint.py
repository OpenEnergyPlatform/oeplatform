"""Button roles (#2641) and the page lint that holds restyled pages to them.

Every action carries one of four roles on itself: primary (solid, one per
view), secondary (a grey outline), danger (outline on the button that opens a
confirmation, solid inside it) and link. Green, cyan, yellow and black are
status colours and never a button's. The page lint (`base/tests/page_lint.py`)
reads each page that has moved onto the house components, as a browser
receives it, and fails on a button without a role, a status colour used as an
action, or a native `confirm(`/`alert(`. A page joins `RESTYLED_PAGES` in the
ticket that moves it and never leaves.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token

from base.tests import TestViewsTestCase
from base.tests.page_lint import ROLES, lint, status_button
from dataedit.models import Dataset, Table, Tag
from modelview.tests.corpus import seed_corpus
from modelview.tests.html import element_markup, elements_with_class


def page(body: str) -> str:
    """A whole page whose own content is `body`."""
    return (
        '<html><body><nav class="navbar"><a class="btn btn-info">Sign Up</a></nav>'
        f'<main id="main-content">{body}</main></body></html>'
    )


class LintTest(SimpleTestCase):
    """The lint itself, on pages planted with each thing it must catch."""

    def test_a_page_keeping_the_rule_passes(self):
        self.assertEqual(
            lint(
                page(
                    '<button type="submit" class="btn btn-primary">Save</button>'
                    '<button type="button" class="btn btn-secondary">Cancel</button>'
                    '<a class="btn btn-outline-danger" href="#">Delete…</a>'
                    '<input type="submit" class="btn btn-danger" value="Delete table">'
                    '<button type="button" class="btn btn-link">Details</button>'
                    '<input type="checkbox" class="form-check-input">'
                )
            ),
            [],
        )

    def test_a_classless_button_fails(self):
        problems = lint(page('<button type="submit">Submit</button>'))

        self.assertEqual(len(problems), 1)
        self.assertIn("no btn and role", problems[0])

    def test_a_classless_submit_input_fails(self):
        problems = lint(page('<input type="submit" value="Add">'))

        self.assertEqual(len(problems), 1)
        self.assertIn('value="Add"', problems[0])

    def test_btn_without_a_role_fails(self):
        self.assertEqual(len(lint(page('<button class="btn">Go</button>'))), 1)

    def test_a_link_styled_as_a_button_without_a_role_fails(self):
        for classes in ("btn", "btn btn-sm", "btn btn-outline-primary"):
            with self.subTest(classes=classes):
                problems = lint(page(f'<a class="{classes}" href="#">Go</a>'))

                self.assertEqual(len(problems), 1, problems)

    def test_a_page_without_its_own_content_is_refused_not_passed(self):
        with self.assertRaises(ValueError):
            lint("<html><body><button>Submit</button></body></html>")

    def test_a_segmented_controls_option_is_a_choice_not_an_action(self):
        self.assertEqual(
            lint(
                page(
                    '<input type="radio" class="btn-check" id="t">'
                    '<label class="btn btn-outline-primary" for="t">Tables</label>'
                )
            ),
            [],
        )

    def test_a_fragment_is_read_whole(self):
        self.assertEqual(len(lint("<button>Save</button>", fragment=True)), 1)

    def test_a_status_colour_fails_on_any_element(self):
        for status in ("success", "info", "dark", "warning", "light"):
            for variant in (f"btn-{status}", f"btn-outline-{status}"):
                with self.subTest(variant=variant):
                    problems = lint(page(f'<a class="btn {variant}" href="#">Go</a>'))

                    self.assertEqual(len(problems), 1, problems)
                    self.assertIn(variant, problems[0])

    def test_a_status_colour_beside_a_role_still_fails(self):
        self.assertTrue(lint(page('<button class="btn btn-primary btn-success">')))

    def test_a_house_components_own_control_needs_no_role(self):
        self.assertEqual(
            lint(
                page(
                    '<button type="button" class="btn-close" aria-label="Close">'
                    '</button><button class="nav-link active">Tab</button>'
                    '<button class="dropdown-item">Item</button>'
                    '<button type="button" class="tag__remove"></button>'
                )
            ),
            [],
        )

    def test_a_name_that_only_contains_a_status_class_passes(self):
        self.assertEqual(
            lint(page('<a class="table-sidebar__btn-info" href="#">Info</a>')), []
        )

    def test_a_native_dialog_in_an_event_handler_fails(self):
        problems = lint(
            page(
                '<button class="btn btn-danger" '
                "onclick=\"return confirm('Delete?')\">Delete</button>"
            )
        )

        self.assertEqual(len(problems), 1)
        self.assertIn("native dialog", problems[0])

    def test_a_native_dialog_in_an_inline_script_fails_wherever_it_is(self):
        for call in ("alert('x')", "window.confirm('x')", "if (confirm ('x'))"):
            with self.subTest(call=call):
                html = page("").replace("</body>", f"<script>{call}</script></body>")

                self.assertEqual(len(lint(html)), 1)

    def test_a_method_or_a_longer_name_is_not_a_native_dialog(self):
        html = page("").replace(
            "</body>",
            "<script>dialog.confirm(x); showAlert(y); $.confirm(z);</script>"
            '<script src="/static/x.js"></script></body>',
        )

        self.assertEqual(lint(html), [])

    def test_hx_confirm_and_data_confirm_ask_the_house_dialog(self):
        self.assertEqual(
            lint(
                page(
                    '<a class="btn btn-outline-danger" hx-delete="/x" '
                    'hx-confirm="It is deleted.">Delete</a>'
                    '<button class="btn btn-outline-danger" '
                    'data-confirm="It is deleted.">Delete</button>'
                )
            ),
            [],
        )

    def test_the_navbar_is_not_the_pages_own_content(self):
        # The navbar's Sign Up is cyan until the user menu (#2644).
        self.assertEqual(lint(page("")), [])


@dataclass
class Page:
    """A restyled page: its URL name, the URL's arguments, filled from the
    fixture's names (`{table}`, `{model}`, ...), and whether to sign in."""

    name: str
    kwargs: dict = field(default_factory=dict)
    logged_in: bool = False
    #: An htmx fragment, which has no shell and so no #main-content.
    fragment: bool = False

    def label(self):
        return " ".join([self.name, *map(str, self.kwargs.values())])


#: Every page that has moved onto the house components, by the ticket that
#: moved it. A page whose actions depend on who is asking is read signed in
#: as the owner of the fixture, which shows the most of them. The pages of
#: ticket 8 of the spec (#2640) join when it lands.
#:
#: Pages #2641 touched that are NOT here yet, and the ticket that brings them:
#: - login:tables, login:datasets: the dashboard's own cell, menu and filter
#:   controls carry no role (#2659);
#: - login:organizations: Create Organization and the help toggle take their
#:   look from container selectors (#2653); its cards' Edit has a role (#2646);
#: - the peer review pages: buttons styled by container selectors (#2658);
#: - dataedit/admin.html and login's activate, detach, generic_form and
#:   oepuser_create_form: no view renders them (dead code, #2660).
RESTYLED_PAGES = (
    # #2645: one tag and status badges
    Page(
        "modelview:show-factsheet",
        {"sheettype": "model", "pk": "{model}"},
        logged_in=True,
    ),
    Page("modelview:modellist", {"sheettype": "model"}),
    Page("modelview:edit", {"sheettype": "model", "pk": "{model}"}, logged_in=True),
    Page("dataedit:tables-in-topic", {"topic": settings.PSEUDO_TOPIC_DRAFT}),
    Page("dataedit:view", {"table": "{table}"}, logged_in=True),
    Page("dataedit:tags", logged_in=True),
    Page("dataedit:dataset-detail", {"dataset_name": "{dataset}"}),
    # #2639: the page header on pages that had none (contact and profile edit
    # are #2641's below too)
    Page("base:about"),
    Page("base:oefamily-sc"),
    Page("base:legal-privacy-policy"),
    Page("base:legal-tou"),
    Page("base:faq"),
    Page("base:discussion"),
    Page("base:project_detail", {"project_id": "open_ego"}),
    # #2641: button roles
    Page("base:contact"),
    Page("base:styleguide"),
    Page("login:settings", {"user_id": "{user}"}, logged_in=True),
    Page("dataedit:topic-list"),
    Page("dataedit:datasets-in-topic", {"topic": settings.PSEUDO_TOPIC_DRAFT}),
    Page("dataedit:meta_edit", {"table": "{table}"}, logged_in=True),
    Page("dataedit:wizard_create", logged_in=True),
    Page("dataedit:wizard_upload", {"table": "{table}"}, logged_in=True),
    Page("login:edit", {"user_id": "{user}"}, logged_in=True),
    Page("login:reviews", {"user_id": "{user}"}, logged_in=True),
    Page("dataedit:table-graph", {"table": "{table}"}, logged_in=True),
    Page("oeo_ext:oeo-ext-plugin-ui-create", logged_in=True, fragment=True),
    Page("modelview:modeladd", {"sheettype": "model"}, logged_in=True),
    Page(
        "modelview:show-factsheet",
        {"sheettype": "framework", "pk": "{framework}"},
        logged_in=True,
    ),
    Page("modelview:modellist", {"sheettype": "framework"}),
    Page(
        "modelview:edit",
        {"sheettype": "framework", "pk": "{framework}"},
        logged_in=True,
    ),
    # #2643: the confirm dialog; its other pages are listed above (the table
    # page, the tag editor, both factsheets)
    Page("dataedit:table-permission", {"table": "{table}"}, logged_in=True),
    # #2648: underline tabs and dropdowns. Its other pages are listed above
    # (the table page, both factsheet editors, Settings, Reviews) or wait for
    # the tickets named in the comment above this tuple (peer review, the
    # dashboard's tables, datasets and organizations tabs).
)


class PageFixture(TestViewsTestCase):
    """One of each thing a restyled page shows: a table the user owns, a
    model and a framework factsheet with a tag, a published dataset."""

    table_name = "test_page_lint_table"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.table = Table.create_with_oedb_table(
            is_sandbox=True,
            name=cls.table_name,
            user=cls.user,
            column_definitions=[],
            constraints_definitions=[],
        )

    @classmethod
    def tearDownClass(cls):
        cls.table.delete()
        super().tearDownClass()

    def setUp(self):
        # Settings shows Reset token only beside a token.
        Token.objects.get_or_create(user=self.user)
        tag = Tag.objects.create(name="Page Lint Wind", color=int("2E7D32", 16))
        self.table.tags.add(tag)
        self.model = seed_corpus("model", factsheets=1, corrupted=0).factsheets[0]
        self.framework = seed_corpus("framework", factsheets=1, corrupted=0).factsheets[
            0
        ]
        for sheet in (self.model, self.framework):
            sheet.tags.add(tag)
        self.dataset = Dataset.objects.create(
            name="page_lint_dataset",
            metadata={"name": "page_lint_dataset", "title": "T", "description": ""},
            creator=self.user,
            published_at=timezone.now(),
        )
        self.dataset.tables.add(self.table)
        self.names = {
            "table": self.table_name,
            "model": self.model.pk,
            "framework": self.framework.pk,
            "dataset": self.dataset.name,
            "user": self.user.pk,
        }

    def html(self, restyled: Page) -> str:
        kwargs = {
            key: value.format(**self.names) if isinstance(value, str) else value
            for key, value in restyled.kwargs.items()
        }
        return self.get(
            restyled.name,
            kwargs=kwargs,
            logged_in=restyled.logged_in,
            expect_status=200,
        ).content.decode()


class RestyledPagesTest(PageFixture):
    def test_every_restyled_page_keeps_the_button_rule(self):
        for restyled in RESTYLED_PAGES:
            with self.subTest(page=restyled.label()):
                problems = lint(self.html(restyled), fragment=restyled.fragment)
                self.assertEqual(problems, [])


def classes_of(markup: str) -> set[str]:
    found = re.search(r'\bclass="([^"]*)"', markup)
    return set(found.group(1).split()) if found else set()


class ClasslessActionsTest(PageFixture):
    """The three actions that rendered with the browser's default paint."""

    def test_the_contact_forms_submit_is_the_pages_primary_action(self):
        html = element_markup(self.html(Page("base:contact")), "main-content")

        submit = re.findall(r'<button\b[^>]*type="submit"[^>]*>', html)
        self.assertEqual(len(submit), 1)
        self.assertLessEqual({"btn", "btn-primary"}, classes_of(submit[0]))

    def test_reset_token_is_a_danger_outline(self):
        # Destructive; the confirm dialog goes in front of it with Settings
        # (#2653).
        html = self.html(Page("login:settings", {"user_id": "{user}"}, True))

        url = reverse("login:reset-token")
        reset = re.findall(r'<button\b[^>]*hx-post="%s"[^>]*>' % url, html)
        self.assertEqual(len(reset), 1)
        reset = reset[0]
        self.assertLessEqual({"btn", "btn-outline-danger"}, classes_of(reset))

    def test_each_permission_add_is_its_forms_primary_action(self):
        html = self.html(Page("dataedit:table-permission", {"table": "{table}"}, True))

        adds = re.findall(r'<input\b[^>]*value="Add"[^>]*>', html)
        self.assertEqual(len(adds), 2)
        for add in adds:
            self.assertLessEqual({"btn", "btn-primary"}, classes_of(add))


class FooterTest(PageFixture):
    def test_the_footer_is_the_blue_band_not_the_secondary_colour(self):
        html = self.html(Page("base:contact"))

        footers = elements_with_class(html, "footer")
        self.assertEqual(len(footers), 1)
        self.assertNotIn("bg-secondary", footers[0])


#: The status colours this ticket took off every action. Yellow and light grey
#: are status colours too (`page_lint.STATUS_COLOURS`), but the peer review
#: pages' yellow saves are toggled by their script and their bar's Quit still
#: extends `.btn-light` (#2658; bootstrap-select's light grey buttons are
#: swapped by script since #2648), so the scan over every template holds only
#: these three; the page lint holds all five.
GONE_COLOURS = status_button(("success", "info", "dark"))

#: Templates that still carry a status colour as an action, and the ticket
#: that removes it. Nothing else may.
STATUS_COLOURS_LEFT = {
    # Sign Up and Sign In are cyan until the navbar's user menu.
    "base/templates/base/_header.html": "#2644",
}

#: Template directories this scan does not read: the React apps' own (out of
#: scope, spec #2632) and anything installed.
NOT_TEMPLATES = ("node_modules", "site-packages", "/frontend/", "/static/")


class NoStatusColourAsAnActionTest(SimpleTestCase):
    """No template draws an action green, cyan or black."""

    def test_no_template_uses_success_info_or_dark_on_a_button(self):
        root = Path(settings.BASE_DIR)
        offenders = []
        for path in sorted(root.rglob("*.html")):
            relative = path.relative_to(root).as_posix()
            if any(part in "/" + relative for part in NOT_TEMPLATES):
                continue
            if relative in STATUS_COLOURS_LEFT:
                continue
            for value in re.findall(r'class="([^"]*)"', path.read_text("utf-8")):
                tokens = " ".join(re.split(r"{%.*?%}|\s+", value))
                if any(GONE_COLOURS.match(token) for token in tokens.split()):
                    offenders.append(f"{relative}: {value}")
        self.assertEqual(offenders, [])

    def test_no_theme_rule_extends_one_onto_a_button(self):
        # A class styled through the theme (`@extend .btn-outline-info`) is
        # invisible to the template scan above.
        root = Path(settings.BASE_DIR) / "theming" / "scss"
        offenders = [
            f"{path.relative_to(root)}: {line.strip()}"
            for path in sorted(root.rglob("*.scss"))
            for line in path.read_text("utf-8").splitlines()
            if (found := re.search(r"@extend \.(btn-[\w-]+)", line))
            and GONE_COLOURS.match(found.group(1))
        ]
        self.assertEqual(offenders, [])

    def test_the_templates_left_still_need_their_ticket(self):
        # When the user menu lands, its ticket deletes the entry above.
        root = Path(settings.BASE_DIR)
        for template in STATUS_COLOURS_LEFT:
            with self.subTest(template=template):
                self.assertRegex((root / template).read_text("utf-8"), r"\bbtn-info\b")


class CatalogueEntryTest(SimpleTestCase):
    def test_the_button_entry_shows_every_role_size_and_state(self):
        entry = (
            Path(settings.BASE_DIR) / "base/templates/styleguide/entries/button.html"
        ).read_text("utf-8")
        shown = {
            token
            for value in re.findall(r'class="([^"]*)"', entry)
            for token in value.split()
        }

        for wanted in (
            "btn-primary",
            "btn-secondary",
            "btn-outline-danger",
            "btn-danger",
            "btn-link",
            "btn-on-strong",
            "btn-sm",
        ):
            with self.subTest(wanted=wanted):
                self.assertIn(wanted, shown)
        self.assertRegex(entry, r"<button\b[^>]*\sdisabled[\s>]")


class SidebarButtonsTest(PageFixture):
    """The table page's sidebar buttons carry their role on themselves, not
    through the sidebar's own classes."""

    def test_every_sidebar_button_has_a_role(self):
        html = self.html(Page("dataedit:view", {"table": "{table}"}))

        sidebar = re.findall(r"<(?:a|button)\b[^>]*table-sidebar__btn[^>]*>", html)
        self.assertTrue(sidebar)
        for button in sidebar:
            with self.subTest(button=button):
                classes = classes_of(button)
                self.assertIn("btn", classes)
                self.assertTrue(classes & ROLES, classes)
