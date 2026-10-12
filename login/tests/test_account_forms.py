"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The account forms on the house field and the button roles (#2642).

Password change, password reset from key and social sign-up are written with
allauth's `{% element %}` tags, which rendered bare `<p>` fields and a
classless button until the OEP overrode the elements (field, fields, form,
button) in login/templates/allauth/elements/. The other account pages keep
their hand-written fields; their buttons and alerts moved from `.login__*`
onto the button roles and the alert component.
"""  # noqa: 501

import re
from pathlib import Path

from allauth.account.forms import default_token_generator
from allauth.account.utils import user_pk_to_url_str
from django import forms
from django.conf import settings
from django.template import Context, Origin, Template
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from base.tests.html_tree import parse
from login.tests.helpers import make_user

PASSWORD = "a-long-test-password"
RETIRED = re.compile(r"login__(?:button|alert)")


def account_column(html):
    return parse(html).find("div", "login__wrap")


def assert_house_form(test, html):
    """Every visible field is a house field below its label, and the form's
    one submit is the primary button."""
    form = account_column(html).find("form")
    fields = [
        node
        for node in form.find_all("input") + form.find_all("textarea")
        if node.attrs.get("type") != "hidden"
    ]
    test.assertTrue(fields)
    labelled = [
        label.attrs.get("for")
        for label in form.find_all("label")
        if label.has_class("form-label")
    ]
    for node in fields:
        with test.subTest(field=node.attrs.get("name")):
            test.assertTrue(node.has_class("form-control"), node.attrs)
            test.assertIn(node.attrs["id"], labelled)
    submit = [
        node for node in form.find_all("button") if node.attrs.get("type") == "submit"
    ]
    test.assertEqual(len(submit), 1)
    test.assertTrue({"btn", "btn-primary"} <= set(submit[0].classes))


class ElementFormsTest(TestCase):
    def setUp(self):
        self.user = make_user("fields_owner")
        self.user.set_password(PASSWORD)
        self.user.save()

    def test_password_change(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("account_change_password"))

        self.assertEqual(response.status_code, 200)
        assert_house_form(self, response.content.decode())

    def test_password_reset_from_key(self):
        key = default_token_generator.make_token(self.user)
        url = reverse(
            "account_reset_password_from_key",
            kwargs={"uidb36": user_pk_to_url_str(self.user), "key": key},
        )

        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)
        assert_house_form(self, response.content.decode())

    def test_social_sign_up(self):
        # The view needs a sign-in in progress with a provider; the page is
        # the template and its form.
        class SignupForm(forms.Form):
            username = forms.CharField()
            email = forms.EmailField()

        request = RequestFactory().get("/")
        request.user = self.user
        html = render_to_string(
            "socialaccount/signup.html", {"form": SignupForm()}, request
        )

        assert_house_form(self, html)

    def test_an_error_marks_its_field_only(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("account_change_password"),
            {"oldpassword": "wrong", "password1": PASSWORD, "password2": PASSWORD},
        )

        tree = account_column(response.content.decode())
        old = [
            n for n in tree.find_all("input") if n.attrs.get("name") == "oldpassword"
        ]
        self.assertTrue(old[0].has_class("is-invalid"))
        self.assertTrue(tree.find_all("div", "invalid-feedback"))
        # A field that passed is not marked green beside it.
        self.assertFalse(tree.find_all(css_class="is-valid"))


class ElementOverridesTest(SimpleTestCase):
    def render(self, source, **context):
        # allauth's element tag reads the template's name.
        origin = Origin("element_test.html", template_name="element_test.html")
        template = Template("{% load allauth %}" + source, origin=origin)
        return template.render(Context(context))

    def test_a_field_with_an_error(self):
        html = self.render(
            '{% element field type="email" id="id_email" name="email" '
            "errors=errors %}{% slot label %}E-Mail{% endslot %}{% endelement %}",
            errors=["Enter a valid email address."],
        )

        tree = parse(html)
        self.assertEqual(tree.find("label").attrs.get("for"), "id_email")
        self.assertTrue(tree.find("label").has_class("form-label"))
        field = tree.find("input")
        self.assertTrue({"form-control", "is-invalid"} <= set(field.classes))
        self.assertIn(
            "Enter a valid email address.", tree.find("div", "invalid-feedback").text()
        )

    def test_a_radio_is_a_form_check(self):
        tree = parse(
            self.render(
                '{% element field type="radio" id="r" name="account" value=1 %}'
                "{% slot label %}GitHub{% endslot %}{% endelement %}"
            )
        )

        self.assertTrue(tree.find("input").has_class("form-check-input"))
        self.assertTrue(tree.find("label").has_class("form-check-label"))

    def test_buttons_take_a_role_from_allauth_s_tags(self):
        for tags, role in (
            ("", "btn-primary"),
            ("prominent,login", "btn-primary"),
            ("secondary", "btn-secondary"),
            ("outline,cancel", "btn-secondary"),
            ("link,cancel", "btn-link"),
            ("danger,delete", "btn-outline-danger"),
        ):
            with self.subTest(tags=tags):
                html = self.render(
                    '{% element button type="submit" tags=tags %}Go{% endelement %}',
                    tags=tags,
                )
                self.assertEqual(parse(html).find("button").classes, ["btn", role])


class RetiredClassesTest(SimpleTestCase):
    def test_no_template_uses_the_login_buttons_or_alerts(self):
        found = [
            str(path.relative_to(settings.BASE_DIR))
            for path in Path(settings.BASE_DIR).glob("*/templates/**/*.html")
            if RETIRED.search(path.read_text())
        ]
        self.assertEqual(found, [])

    def test_nor_does_the_theme(self):
        theme = Path(settings.BASE_DIR) / "theming" / "scss"
        found = [
            str(path)
            for path in theme.rglob("*.scss")
            if RETIRED.search(path.read_text())
        ]
        self.assertEqual(found, [])


class FieldPartialTest(SimpleTestCase):
    """The house rule, on the field's own partial: no shorthand that also sets
    what Bootstrap keeps for the select's arrow or the field's box."""

    SHORTHANDS = re.compile(r"^\s*(?:padding|margin|background|border|font)\s*:", re.M)

    def test_it_sets_longhands_only(self):
        partial = (
            Path(settings.BASE_DIR) / "theming" / "scss" / "components" / "_field.scss"
        )
        self.assertEqual(self.SHORTHANDS.findall(partial.read_text()), [])
