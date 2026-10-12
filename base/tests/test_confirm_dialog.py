"""The confirm dialog and the toast region (#2643, spec #2632): one dialog asks
every confirmation and one region shows every toast, in every shell; no
template or platform script calls the browser's `confirm()` or `alert()`.

What the dialog does (answers, focus, htmx) is proved by the module's own
suite, `base/static/base/__tests__/dialogs.test.js`. Here: that every page
carries the pieces, and that each former native dialog now asks the house
one, as a browser receives the pages.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase

from base.tests.html_tree import parse
from base.tests.page_lint import NATIVE_DIALOG
from base.tests.test_instance_theming import ShellPagesTestCase
from base.tests.test_page_lint import Page, PageFixture
from login.models import UserPermission
from login.models import myuser as User
from login.permissions import ADMIN_PERM
from modelview.tests.html import element_markup

ROOT = Path(settings.BASE_DIR)

#: Not the platform's own: installed packages, the React apps (out of scope,
#: spec #2632), tests, and vendored libraries. htmx calls `confirm()` itself
#: only when nothing answers its `htmx:confirm` event, which the shell's
#: module always does.
NOT_OURS = ("node_modules", "site-packages", "/frontend/", "__tests__", "/vendor/")
VENDORED = {
    "ontology/static/ontology/htmx.js",
    "dataedit/static/dataedit/query-builder.standalone.js",
    "base/static/js/jsi18n.js",
}

TEMPLATE_COMMENT = re.compile(
    r"{#.*?#}|{% comment %}.*?{% endcomment %}|<!--.*?-->", re.S
)
SCRIPT_COMMENT = re.compile(r"/\*.*?\*/|(?<![:\\])//[^\n]*", re.S)


def select(html, tag=None, **attrs):
    """The elements of `html` with `tag` whose attributes hold `attrs`
    (`class_` is one class among theirs; None asks only that it is there)."""
    css_class = attrs.pop("class_", None)
    return [
        node
        for node in parse(html).find_all(tag, css_class)
        if all(
            name in node.attrs and (value is None or node.attrs[name] == value)
            for name, value in attrs.items()
        )
    ]


def ours(path):
    relative = path.relative_to(ROOT).as_posix()
    return not (
        relative.startswith("static/")
        or relative.endswith(".min.js")
        or relative in VENDORED
        or any(part in "/" + relative for part in NOT_OURS)
    )


def templates():
    return [p for p in sorted(ROOT.glob("*/templates/**/*.html")) if ours(p)]


def scripts():
    return [p for p in sorted(ROOT.glob("*/static/**/*.js")) if ours(p)]


class NoNativeDialogTest(SimpleTestCase):
    def test_no_template_calls_confirm_or_alert(self):
        offenders = [
            path.relative_to(ROOT).as_posix()
            for path in templates()
            if NATIVE_DIALOG.search(TEMPLATE_COMMENT.sub("", path.read_text("utf-8")))
        ]
        self.assertEqual(offenders, [])

    def test_no_platform_script_calls_confirm_or_alert(self):
        found = scripts()
        self.assertIn(ROOT / "dataedit/static/dataedit/backend.js", found)
        offenders = [
            path.relative_to(ROOT).as_posix()
            for path in found
            if NATIVE_DIALOG.search(SCRIPT_COMMENT.sub("", path.read_text("utf-8")))
        ]
        self.assertEqual(offenders, [])

    def test_the_scan_sees_a_call(self):
        self.assertTrue(NATIVE_DIALOG.search(SCRIPT_COMMENT.sub("", "if (confirm(x))")))
        self.assertFalse(NATIVE_DIALOG.search(SCRIPT_COMMENT.sub("", "// confirm(x)")))

    def test_every_hx_confirm_names_its_action_and_its_verb(self):
        for path in templates():
            source = path.read_text("utf-8")
            for start in re.finditer(r"<[a-z]+\b[^>]*\bhx-confirm=", source):
                tag = source[start.start() : source.index(">", start.end())]
                with self.subTest(template=path.relative_to(ROOT).as_posix()):
                    self.assertIn("data-confirm-title=", tag)
                    self.assertIn("data-confirm-verb=", tag)

    def test_no_page_keeps_its_own_toast_container_or_delete_modal(self):
        retired = re.compile(
            r"z-index: ?11\b|liveToast|dataview-confirm-delete|wizard-confirm-delete"
        )
        offenders = [
            path.relative_to(ROOT).as_posix()
            for path in [*templates(), *scripts()]
            if retired.search(path.read_text("utf-8"))
        ]
        self.assertEqual(offenders, [])


class ShellTest(ShellPagesTestCase):
    """Every shell renders one dialog, one toast region and the module."""

    def test_every_shell_renders_one_dialog_and_one_toast_region(self):
        for shell, view_name, kwargs, logged_in in self.pages():
            with self.subTest(shell=shell):
                html = self.page(view_name, kwargs=kwargs, logged_in=logged_in)

                self.assertEqual(len(select(html, id="confirm-dialog")), 1)
                self.assertEqual(len(select(html, class_="toast-region")), 1)
                self.assertEqual(len(select(html, id="toast-template")), 1)
                self.assertEqual(html.count("base/dialogs.js"), 1)

    def test_the_dialogs_buttons_are_cancel_and_the_verb(self):
        (dialog,) = select(self.page("base:about"), id="confirm-dialog")

        cancel, accept = dialog.find_all("button", "btn")
        self.assertEqual(cancel.text(), "Cancel")
        self.assertIn("btn-secondary", cancel.classes)
        self.assertIn("data-confirm-accept", accept.attrs)


class IncludeTest(SimpleTestCase):
    def render(self, name, **context):
        return render_to_string(f"components/{name}.html", context)

    def test_the_verb_is_solid_danger_only_when_irreversible(self):
        for danger, role in ((True, "btn-danger"), (False, "btn-primary")):
            with self.subTest(danger=danger):
                html = self.render("confirm_dialog", verb="Delete", danger=danger)
                (accept,) = select(html, **{"data-confirm-accept": None})
                self.assertIn(role, accept.classes)
                self.assertEqual(accept.text(), "Delete")

    def test_a_typed_confirmation_shows_its_input_and_starts_disabled(self):
        html = self.render("confirm_dialog", typed="wind_farms", as_example=True)

        (typed,) = select(html, **{"data-confirm-typed": None})
        (accept,) = select(html, **{"data-confirm-accept": None})
        self.assertNotIn("hidden", typed.attrs)
        self.assertIn("disabled", accept.attrs)
        # the catalogue's copies carry no id the shell's instance has
        self.assertEqual(select(html, id=None), [])

    def test_a_toast_carries_its_status_and_escapes_its_text(self):
        html = self.render("toast", status="danger", text="<b>x</b>")

        self.assertIn("toast--danger", html)
        self.assertNotIn("<b>", html)


class FormerNativeDialogsTest(PageFixture):
    """Each former native dialog, as its page renders it."""

    def opener(self, html, **attrs):
        found = select(html, **attrs)
        self.assertEqual(len(found), 1, attrs)
        return found[0]

    def test_a_factsheet_delete_asks_the_dialog(self):
        for sheettype in ("model", "framework"):
            with self.subTest(sheettype=sheettype):
                html = self.html(
                    Page(
                        "modelview:show-factsheet",
                        {"sheettype": sheettype, "pk": "{%s}" % sheettype},
                        logged_in=True,
                    )
                )
                delete = self.opener(html, **{"hx-delete": None})

                self.assertIn("hx-confirm", delete.attrs)
                self.assertIn("data-confirm-danger", delete.attrs)
                self.assertIn("btn-outline-danger", delete.classes)

    def test_the_table_view_delete_asks_the_dialog_and_has_no_modal(self):
        html = self.html(Page("dataedit:view", {"table": "{table}"}, logged_in=True))

        delete = self.opener(html, id="dataview-table-delete")
        self.assertIn(self.table_name, delete.attrs["data-confirm"])
        self.assertEqual(delete.attrs["data-confirm-verb"], "Delete table")
        self.assertIn("data-confirm-danger", delete.attrs)
        self.assertEqual(
            select(element_markup(html, "main-content"), class_="modal"), []
        )

    def test_the_wizard_has_no_modal_of_its_own(self):
        html = self.html(Page("dataedit:wizard_create", logged_in=True))

        self.assertEqual(
            select(element_markup(html, "main-content"), class_="modal"), []
        )

    def test_removing_a_permission_holder_asks_the_dialog(self):
        other = User.objects.create_user(
            name="other_holder", email="other@test.test", affiliation="test"
        )
        UserPermission.objects.create(table=self.table, holder=other, level=ADMIN_PERM)
        html = self.html(
            Page("dataedit:table-permission", {"table": "{table}"}, logged_in=True)
        )

        removes = select(html, "input", value="Remove user")
        asking = [r for r in removes if "data-confirm" in r.attrs]
        self.assertEqual(len(asking), 1)
        self.assertIn("other_holder", asking[0].attrs["data-confirm"])
        self.assertNotIn("onsubmit", html)

    def test_deleting_a_tag_asks_the_dialog(self):
        self.user.is_admin = True
        self.user.save()
        tag = self.table.tags.first()
        html = self.get(
            "dataedit:tags-edit", kwargs={"tag_pk": tag.pk}, logged_in=True
        ).content.decode()

        delete = self.opener(html, name="submit_delete")
        self.assertIn("removed from 3 object", delete.attrs["data-confirm"])
        self.assertEqual(delete.attrs["data-confirm-verb"], "Delete tag")
