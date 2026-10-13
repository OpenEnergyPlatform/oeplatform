"""The Manage Profile card edits in place on Settings (#2654).

htmx swaps the card between reading and editing, so the address stays
Settings: an htmx edit request answers the card alone, a valid htmx save
redirects to Settings (whose card the request selects), an invalid one answers
the card with its errors. Without htmx the edit address is a page of its own in
the Settings layout, and a save keeps its redirect to the dashboard.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse

from base.tests import TestViewsTestCase
from base.tests.html_tree import parse
from base.tests.page_lint import lint
from base.tests.test_page_header import AREA, bands_of, trail_items

HTMX = {"HTTP_HX_REQUEST": "true"}
CARD = "profile-card"
SWAP = {"hx-target": f"#{CARD}", "hx-select": f"#{CARD}", "hx-swap": "outerHTML"}


class EditInPlaceTest(TestViewsTestCase):
    def url(self, name):
        return reverse(f"login:{name}", kwargs={"user_id": self.user.pk})

    def send(self, method, name, htmx=False, **data):
        self.client.force_login(self.user)
        return getattr(self.client, method)(
            self.url(name), data or None, **(HTMX if htmx else {})
        )

    def card(self, html):
        return first(parse(html), id=CARD)

    def assert_swaps_in_place(self, card):
        for name, value in SWAP.items():
            self.assertEqual(card.attrs.get(name), value)
        self.assertIn("data-edit-in-place", card.attrs)

    def test_settings_shows_the_card_reading(self):
        card = self.card(self.send("get", "settings").content.decode())
        self.assert_swaps_in_place(card)
        self.assertIsNone(card.find("form"))
        edit = first(card, **{"data-edit-in-place-trigger": None})
        self.assertEqual(edit.text(), "Edit")
        self.assertEqual(edit.attrs["href"], self.url("edit"))
        self.assertEqual(edit.attrs["hx-get"], self.url("edit"))
        self.assertEqual(set(edit.classes), {"btn", "btn-primary"})

    def test_an_htmx_edit_request_answers_the_form_fragment(self):
        response = self.send("get", "edit", htmx=True)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertNotIn("<html", html)
        self.assertNotIn("page-header", html)
        card = self.card(html)
        self.assert_swaps_in_place(card)
        form = card.find("form")
        self.assertEqual(form.attrs["hx-post"], self.url("edit"))
        self.assertEqual(form.attrs["action"], self.url("edit"))
        self.assertEqual(form.attrs["enctype"], "multipart/form-data")

    def test_the_fragment_passes_the_page_lint(self):
        html = self.send("get", "edit", htmx=True).content.decode()
        self.assertEqual(lint(html, fragment=True), [])

    def test_the_form_has_cancel_and_submit_and_house_fields(self):
        card = self.card(self.send("get", "edit", htmx=True).content.decode())
        cancel, submit = card.find("form").find_all(css_class="btn")
        self.assertEqual(cancel.text(), "Cancel")
        self.assertEqual(set(cancel.classes), {"btn", "btn-secondary"})
        self.assertEqual(cancel.attrs["href"], self.url("settings"))
        self.assertEqual(cancel.attrs["hx-get"], self.url("settings"))
        self.assertEqual(submit.text(), "Submit")
        self.assertEqual(set(submit.classes), {"btn", "btn-primary"})
        # {% bootstrap_field %}: the label above its own field.
        label = first(card, tag="label", **{"for": "id_fullname"})
        self.assertEqual(label.attrs.get("class"), "form-label")

    def test_a_valid_htmx_save_redirects_to_settings(self):
        response = self.send("post", "edit", htmx=True, fullname="In Place")
        self.assertRedirects(response, self.url("settings"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.fullname, "In Place")

    def test_a_plain_save_keeps_its_redirect(self):
        response = self.send("post", "edit", fullname="Plain")
        self.assertRedirects(
            response, self.url("profile"), fetch_redirect_response=False
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.fullname, "Plain")

    def test_an_invalid_htmx_save_answers_the_card_with_its_errors(self):
        response = self.send("post", "edit", htmx=True, linkedin="not an address")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertNotIn("<html", html)
        card = self.card(html)
        self.assertIsNotNone(card.find("form"))
        field = first(card, tag="input", name="linkedin")
        self.assertIn("is-invalid", field.classes)
        self.assertIsNotNone(card.find(css_class="invalid-feedback"))
        self.user.refresh_from_db()
        self.assertIsNone(self.user.linkedin)

    def test_an_invalid_plain_save_renders_the_page_with_its_errors(self):
        response = self.send("post", "edit", linkedin="not an address")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(bands_of(parse(response.content.decode()))), 1)
        self.assertIn("is-invalid", response.content.decode())

    def test_the_standalone_page_is_the_card_in_the_settings_layout(self):
        root = parse(self.send("get", "edit").content.decode())
        (band,) = bands_of(root)
        self.assertEqual(band.find(css_class=AREA).text(), "Account")
        _nav, _ordered, items = trail_items(band)
        self.assertEqual(
            [i.text() for i in items],
            ["Dashboard", "Settings", "Update account profile"],
        )
        self.assertIsNotNone(first(root.find(css_class="account-cards"), id=CARD))
        self.assertIsNotNone(first(root, id=CARD).find("form"))


def first(root, tag=None, **attrs):
    """The first element below `root` carrying `attrs` (a bare attribute: None)."""
    for node in root.iter():
        if (tag is None or node.tag == tag) and all(
            name in node.attrs and node.attrs[name] == value
            for name, value in attrs.items()
        ):
            return node
    return None
