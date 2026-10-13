"""The factsheet editors and lists on house components (#2656), as a browser
receives them.

The editors used to lay their 171 fields out in a table (`formtable`), the
label in a fifth of the width so that long ones wrapped into five lines, with
"Submit all" in the tab row, bare checkboxes, an invalid `<sup color>` and a
green "+" / red "x" drawn by inline colours. Now every field is one block with
its label above it, a group of checkboxes is a fieldset, and the save action
sits below the tabs. What it looks like is the theme's and the page CSS's,
checked in the browser rather than here.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from base.tests import TestViewsTestCase
from base.tests.html_tree import parse
from modelview.tests.corpus import seed_corpus

SHEETTYPES = ("model", "framework")

#: Fields the framework editor renders twice: its "Software" pane has no tab
#: (since #559) and repeats them. Not this ticket's to remove: the pane also
#: posts four fields no other tab holds, so dropping it would empty them.
RENDERED_TWICE = {"id_gui"}

#: An inline colour, but not a tag's `--tag-color` custom property.
INLINE_COLOUR = re.compile(r"(?<![\w-])color\s*:")


class EditorPages(TestViewsTestCase):
    """Both editors, editing and creating, as their forms."""

    def setUp(self):
        self.corpus = {
            t: seed_corpus(sheettype=t, factsheets=1, corrupted=0) for t in SHEETTYPES
        }

    def pages(self):
        for sheettype in SHEETTYPES:
            sheet = self.corpus[sheettype].factsheets[0]
            for name, kwargs in (
                ("edit", {"view_name": "modelview:edit", "pk": sheet.pk}),
                ("add", {"view_name": "modelview:modeladd"}),
            ):
                view_name = kwargs.pop("view_name")
                html = self.get(
                    view_name, kwargs={"sheettype": sheettype, **kwargs}, logged_in=True
                ).content.decode("utf-8")
                yield f"{sheettype} {name}", parse(html)

    def form(self, root):
        forms = [n for n in root.iter() if n.attrs.get("id") == "factsheet-form"]
        self.assertEqual(len(forms), 1)
        return forms[0]


class SaveActionTest(EditorPages):
    def test_one_primary_save_below_the_tabs(self):
        for page, root in self.pages():
            with self.subTest(page=page):
                form = self.form(root)
                submits = [
                    n
                    for n in form.iter()
                    if n.tag in ("input", "button") and n.attrs.get("type") == "submit"
                ]
                self.assertEqual(len(submits), 1)
                save = submits[0]
                self.assertIn("btn-primary", save.classes)
                row = form.find(css_class="tabs")
                self.assertFalse(save.within(row), "the save action is in the tab row")
                self.assertTrue(
                    any(a.has_class("factsheet-form__actions") for a in save.ancestors)
                )


class FieldLayoutTest(EditorPages):
    def test_no_table_lays_the_form_out(self):
        for page, root in self.pages():
            with self.subTest(page=page):
                self.assertEqual(self.form(root).find_all("table"), [])

    def test_every_checkbox_is_a_form_check_with_its_label(self):
        for page, root in self.pages():
            with self.subTest(page=page):
                form = self.form(root)
                labels = {
                    n.attrs.get("for"): n
                    for n in form.find_all("label", "form-check-label")
                }
                boxes = [
                    n
                    for n in form.find_all("input")
                    if n.attrs.get("type") == "checkbox"
                    and not n.has_class("tag__check")  # the tag picker's own (#2645)
                ]
                self.assertTrue(boxes)
                for box in boxes:
                    self.assertIn("form-check-input", box.classes, box.attrs)
                    self.assertTrue(box.parent.has_class("form-check"), box.attrs)
                    self.assertIn(box.attrs["id"], labels, box.attrs)

    def test_every_label_points_at_one_field_and_no_field_has_two(self):
        for page, root in self.pages():
            with self.subTest(page=page):
                form = self.form(root)
                ids = {n.attrs.get("id") for n in form.iter()}
                # A tag toggle's label wraps its box and names no target.
                pointed = [
                    n.attrs["for"] for n in form.find_all("label") if n.attrs.get("for")
                ]
                for target in pointed:
                    self.assertIn(target, ids)
                self.assertEqual(
                    {t for t in pointed if pointed.count(t) > 1} - RENDERED_TWICE,
                    set(),
                    "two labels",
                )

    def test_a_required_list_field_is_marked(self):
        for page, root in self.pages():
            with self.subTest(page=page):
                label = [
                    n
                    for n in self.form(root).iter()
                    if n.attrs.get("id") == "contact_email_label"
                ]
                self.assertEqual(label[0].text(), "Contact (e-mail) *")

    def test_every_label_opens_its_own_field_block(self):
        for page, root in self.pages():
            with self.subTest(page=page):
                for label in self.form(root).find_all("label", "form-label"):
                    self.assertTrue(label.parent.has_class("factsheet-field"))

    def test_groups_of_choices_are_fieldsets(self):
        for page, root in self.pages():
            with self.subTest(page=page):
                groups = self.form(root).find_all("fieldset", "factsheet-group")
                self.assertTrue(groups)
                for group in groups:
                    self.assertEqual(group.elements[0].tag, "legend")


class NoInlineDrawingTest(EditorPages):
    def test_no_style_element_sup_or_inline_colour(self):
        for page, root in self.pages():
            with self.subTest(page=page):
                main = root.find("main")
                self.assertEqual(main.find_all("style"), [])
                self.assertEqual(main.find_all("sup"), [])
                for node in main.iter():
                    style = node.attrs.get("style") or ""
                    self.assertIsNone(INLINE_COLOUR.search(style), node.attrs)

    def test_array_entries_are_added_by_a_house_button(self):
        for page, root in self.pages():
            with self.subTest(page=page):
                adds = [
                    n
                    for n in self.form(root).find_all("button")
                    if n.attrs.get("aria-label") == "Add an entry"
                ]
                self.assertTrue(adds)
                for add in adds:
                    self.assertIn("btn-secondary", add.classes)


class ListPageTest(TestViewsTestCase):
    def test_field_toggles_are_form_checks_without_inline_styles(self):
        for sheettype in SHEETTYPES:
            with self.subTest(sheettype=sheettype):
                seed_corpus(sheettype=sheettype, factsheets=1, corrupted=0)
                root = parse(
                    self.get(
                        "modelview:modellist", kwargs={"sheettype": sheettype}
                    ).content.decode("utf-8")
                )
                fields = root.find(css_class="checkbox-container")
                boxes = [
                    n
                    for n in fields.find_all("input")
                    if n.attrs.get("type") == "checkbox"
                ]
                self.assertTrue(boxes)
                for box in boxes:
                    self.assertIn("form-check-input", box.classes)
                    self.assertTrue(box.parent.has_class("form-check"))
                self.assertEqual(
                    [n.attrs for n in fields.iter() if "style" in n.attrs], []
                )
                self.assertEqual(root.find("main").find_all("style"), [])


class NoTableLayoutLeftTest(SimpleTestCase):
    def test_no_modelview_source_names_the_table_layout(self):
        root = Path(settings.BASE_DIR, "modelview")
        found = [
            str(path)
            for pattern in ("templates/**/*.html", "static/**/*.css")
            for path in root.glob(pattern)
            if any(
                c in path.read_text(encoding="utf-8")
                for c in ("formtable", "checktable")
            )
        ]
        self.assertEqual(found, [])
