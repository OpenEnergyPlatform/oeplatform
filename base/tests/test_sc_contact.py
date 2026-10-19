"""Steering committee and contact (#2651, spec #2632, WF-13).

The steering committee reads as a reading column with its members listed in
text columns: each member's name, then their institution, each in an element
of its own so the page can weigh them differently. The contact form renders
field by field through django-bootstrap5, with Name and E-Mail on one row,
the captcha image and its input in one field, and the GitHub line as a card
in the side column; it still sends the message it sent before.

Structure only, never CSS: that the members fall into three columns at 1440 px
and one at 390 px is measured in a browser and shown in the pull request.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from captcha.models import CaptchaStore
from django.core import mail

from base.forms import ContactForm
from base.tests import TestViewsTestCase
from base.tests.html_tree import parse
from oeplatform.settings import CONTACT_ADDRESSES

MEMBERS = 16


def named(root, name):
    """The form control called `name`."""
    return next(n for n in root.iter() if n.attrs.get("name") == name)


class SteeringCommitteeTest(TestViewsTestCase):
    def page(self):
        return parse(self.get("base:oefamily-sc", expect_status=200).content.decode())

    def test_the_text_sits_in_a_reading_column(self):
        main = self.page().find(css_class="content__main")
        column = main.find(css_class="reading-column")
        self.assertEqual(
            [h.text() for h in main.find_all("h2")],
            [
                "What is the Steering Committee?",
                "Who is involved?",
            ],
        )
        for heading in main.find_all("h2"):
            self.assertTrue(heading.within(column))

    def test_each_member_is_a_name_then_an_institution(self):
        members = self.page().find("ul", "member-list").elements
        self.assertEqual(len(members), MEMBERS)
        for member in members:
            with self.subTest(member=member.text()):
                parts = member.elements
                self.assertTrue(parts[0].has_class("member-list__name"))
                self.assertTrue(
                    all(p.has_class("member-list__institution") for p in parts[1:])
                )
                self.assertLessEqual(len(parts), 2)
        # One member names no institution.
        alone = [m for m in members if len(m.elements) == 1]
        self.assertEqual([m.text() for m in alone], ["Robbie Morrison"])


class ContactPageTest(TestViewsTestCase):
    def page(self):
        return parse(self.get("base:contact", expect_status=200).content.decode())

    def test_name_and_email_share_a_row_and_topic_follows_them(self):
        form = self.page().find("form")
        fields = [
            node.attrs["name"]
            for node in form.iter()
            if (node.attrs.get("name") or "").startswith(("contact_", "content"))
        ]
        self.assertEqual(
            fields,
            [
                "contact_category",
                "contact_name",
                "contact_email",
                "contact_topic",
                "content",
            ],
        )
        name = named(form, "contact_name")
        email = named(form, "contact_email")
        topic = named(form, "contact_topic")
        row = next(a for a in name.ancestors if a.has_class("row"))
        self.assertTrue(email.within(row))
        self.assertFalse(topic.within(row))

    def test_every_field_of_the_form_renders(self):
        # The template names the fields one by one, so a field added to the
        # form must be added there too, or the form could never validate.
        form = self.page().find("form")
        rendered = {n.attrs.get("name") or "" for n in form.iter()}
        for name in ContactForm.base_fields:
            with self.subTest(field=name):
                # A multi-part field (the captcha) renders as name_0, name_1.
                self.assertTrue(
                    any(r == name or r.startswith(name + "_") for r in rendered)
                )

    def test_the_captcha_image_and_its_input_are_one_field(self):
        form = self.page().find("form")
        image = form.find("img", "captcha")
        answer = named(form, "captcha_1")
        field = next(a for a in answer.ancestors if a.has_class("captcha-field"))
        self.assertTrue(image.within(field))
        self.assertEqual(field.find("label").attrs.get("for"), "id_captcha_1")

    def test_one_primary_submit(self):
        submits = [
            b
            for b in self.page().find("form").find_all("button")
            if b.attrs.get("type") == "submit"
        ]
        self.assertEqual(len(submits), 1)
        self.assertTrue({"btn", "btn-primary"} <= set(submits[0].classes))

    def test_the_old_wrappers_are_gone(self):
        main = self.page().find(css_class="content")
        self.assertIsNone(main.find("table"))
        self.assertIsNone(main.find(css_class="well"))
        self.assertEqual([n.tag for n in main.iter() if "style" in n.attrs], [])

    def test_the_github_line_is_a_card_in_the_side_column(self):
        side = self.page().find("aside", "content__side")
        card = side.find(css_class="card")
        self.assertIn("issue tracking system", card.text())
        self.assertIsNotNone(card.find("a"))


class ContactPostTest(TestViewsTestCase):
    def data(self, **changes):
        captcha = CaptchaStore.objects.create(challenge="ABCD", response="abcd")
        data = {
            "contact_category": "other",
            "contact_name": "Ada",
            "contact_email": "ada@example.org",
            "contact_topic": "A question",
            "content": "Hello there",
            "captcha_0": captcha.hashkey,
            "captcha_1": "abcd",
        }
        return {**data, **changes}

    def test_a_valid_message_is_sent_as_before(self):
        response = self.post("base:contact", data=self.data(), expect_status=200)

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.subject, "A question")
        self.assertEqual(sent.to, list(CONTACT_ADDRESSES["other"]))
        self.assertEqual(sent.body, "Ada (ada@example.org) wrote: \nHello there")
        alert = parse(response.content.decode()).find(css_class="alert-success")
        self.assertEqual(alert.text(), "Success! Your message has been sent.")
        self.assertEqual(alert.attrs.get("role"), "status")

    def test_a_wrong_captcha_sends_nothing_and_marks_the_field(self):
        response = self.post("base:contact", data=self.data(captcha_1="nope"))

        self.assertEqual(mail.outbox, [])
        root = parse(response.content.decode())
        self.assertIsNone(root.find(css_class="alert-success"))
        answer = named(root, "captcha_1")
        self.assertIn("is-invalid", answer.classes)
