"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from captcha.fields import CaptchaField
from django import forms
from django_bootstrap5.renderers import FieldRenderer


class HouseFieldRenderer(FieldRenderer):
    """django-bootstrap5's field, marking an error only: a bound field without
    one stays as it was instead of turning green (`is-valid`)."""

    def get_server_side_validation_classes(self):
        return "is-invalid" if self.field_errors else ""


class ContactForm(forms.Form):
    contact_category = forms.ChoiceField(
        required=True,
        label="Category",
        choices=(("technical", "Technical issues"), ("other", "Other")),
    )
    contact_name = forms.CharField(required=True, label="Name")
    contact_topic = forms.CharField(required=True, label="Topic")
    contact_email = forms.EmailField(required=True, label="E-Mail")
    content = forms.CharField(
        required=True, widget=forms.Textarea, label="Your message"
    )
    captcha = CaptchaField()
