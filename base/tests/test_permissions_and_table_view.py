"""The table permission page and the table view on house components (#2657,
spec #2632), as a browser receives them.

Permissions: house selects and buttons with roles, no Bootstrap 4
`form-inline`, no inline positioning, empty lists as the empty state, and
every removal asked in the house dialog, the question the permission service
asks about the viewer's own role included. Table view: no Bootstrap 3 panel
around the filter and no glyphicons; the vendored query builder gets the
platform's icons through its own `icons` option.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from pathlib import Path

from django.conf import settings

from base.tests.test_confirm_dialog import select
from base.tests.test_page_lint import Page, PageFixture
from login.models import UserPermission
from login.models import myuser as User
from login.permissions import ADMIN_PERM, WRITE_PERM
from modelview.tests.html import element_markup

PERMISSIONS = Page("dataedit:table-permission", {"table": "{table}"}, logged_in=True)
TABLE_VIEW = Page("dataedit:view", {"table": "{table}"}, logged_in=True)
ROOT = Path(settings.BASE_DIR)


class PermissionPageTest(PageFixture):
    def main(self, html):
        return element_markup(html, "main-content")

    def test_every_select_and_field_is_a_house_field(self):
        UserPermission.objects.create(
            table=self.table,
            holder=User.objects.create_user(
                name="field_holder", email="f@test.test", affiliation="test"
            ),
            level=WRITE_PERM,
        )
        main = self.main(self.html(PERMISSIONS))

        selects = select(main, "select")
        self.assertGreaterEqual(len(selects), 3)
        for found in selects:
            self.assertIn("form-select", found.classes, found.attrs)
        (name,) = select(main, "input", id="user_field")
        self.assertIn("form-control", name.classes)

    def test_no_bootstrap_4_inline_form_and_no_inline_positioning(self):
        main = self.main(self.html(PERMISSIONS))

        self.assertNotIn("form-inline", main)
        for styled in select(main, style=None):
            self.assertNotRegex(
                styled.attrs["style"], r"position|float|display", styled.attrs
            )

    def test_an_empty_list_is_the_empty_state(self):
        main = self.main(self.html(PERMISSIONS))

        empty = [
            node
            for node in select(main, class_="empty-state")
            if "No permissions for groups set, yet." in node.text()
        ]
        self.assertEqual(len(empty), 1)
        # the owner holds Admin, so the user list is not empty
        self.assertNotIn("No permissions for users set, yet.", main)

    def test_removing_someone_else_asks_the_dialog(self):
        UserPermission.objects.create(
            table=self.table,
            holder=User.objects.create_user(
                name="other_admin", email="o@test.test", affiliation="test"
            ),
            level=ADMIN_PERM,
        )
        main = self.main(self.html(PERMISSIONS))

        (remove,) = [
            r
            for r in select(main, "input", value="Remove user")
            if "data-confirm" in r.attrs
        ]
        self.assertIn("other_admin", remove.attrs["data-confirm"])
        self.assertEqual(remove.attrs["data-confirm-verb"], "Remove user")
        self.assertIn("data-confirm-danger", remove.attrs)
        self.assertLessEqual({"btn", "btn-outline-danger"}, set(remove.classes))

    def test_the_services_question_about_your_own_role_is_asked_in_the_dialog(
        self,
    ):
        # A second admin, so the owner may give up their own Admin.
        UserPermission.objects.create(
            table=self.table,
            holder=User.objects.create_user(
                name="second_admin", email="s@test.test", affiliation="test"
            ),
            level=ADMIN_PERM,
        )
        for mode, data, verb in (
            ("remove_user", {}, "Remove"),
            ("alter_user", {"level": WRITE_PERM}, "Change role"),
        ):
            with self.subTest(mode=mode):
                html = self.post(
                    "dataedit:table-permission",
                    data={"mode": mode, "user_id": self.user.pk, **data},
                    kwargs={"table": self.table_name},
                    logged_in=True,
                    expect_status=200,
                ).content.decode()

                (confirm,) = select(html, "input", id="permission-confirm")
                question = response_text(html, "permission-confirm-text")
                self.assertEqual(confirm.attrs["data-confirm"], question)
                self.assertEqual(confirm.attrs["data-confirm-verb"], verb)
                self.assertIn("data-confirm-danger", confirm.attrs)
                self.assertLessEqual(
                    {"btn", "btn-outline-danger"}, set(confirm.classes)
                )
                # asked at once, not after a second click
                self.assertRegex(
                    html,
                    r'getElementById\("permission-confirm"\)\.click\(\)',
                )

    def test_no_question_no_script_that_asks_it(self):
        self.assertNotIn("permission-confirm", self.html(PERMISSIONS))


def response_text(html, element_id):
    return re.sub(r"\s+", " ", select(html, id=element_id)[0].text()).strip()


class TableViewTest(PageFixture):
    def test_no_bootstrap_3_panel_and_no_glyphicon(self):
        html = self.html(TABLE_VIEW)

        self.assertNotRegex(html, r'class="[^"]*\bpanel(-[\w-]+)?\b')
        self.assertNotIn("glyphicon", html)

    def test_the_filter_opens_from_a_secondary_button(self):
        main = element_markup(self.html(TABLE_VIEW), "main-content")

        (toggle,) = select(main, "button", **{"aria-controls": "collapseBuilder"})
        self.assertLessEqual({"btn", "btn-secondary"}, set(toggle.classes))
        self.assertEqual(toggle.attrs["data-bs-toggle"], "collapse")
        self.assertEqual(len(select(main, id="builder")), 1)

    def test_the_query_builder_gets_an_icon_for_every_one_it_draws(self):
        # The vendored builder's defaults are glyphicons, which the platform
        # does not load; backend.js names a Font Awesome icon for each.
        vendored = (
            ROOT / "dataedit/static/dataedit/query-builder.standalone.js"
        ).read_text()
        defaults = re.search(r"icons: \{(.*?)\}", vendored, re.S).group(1)
        keys = set(re.findall(r"(\w+): 'glyphicon", defaults))
        self.assertTrue(keys)

        backend = (ROOT / "dataedit/static/dataedit/backend.js").read_text()
        ours = re.search(r"queryBuilder\(\{.*?icons: \{(.*?)\}", backend, re.S)
        self.assertIsNotNone(ours)
        given = dict(re.findall(r'(\w+): "([^"]+)"', ours.group(1)))
        self.assertEqual(set(given), keys)
        for icon in given.values():
            self.assertRegex(icon, r"^fas fa-[\w-]+$")
