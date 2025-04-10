# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
# SPDX-FileCopyrightText: 2025 MGlauer <martinglauer89@gmail.com>
#
# SPDX-License-Identifier: MIT

from captcha.fields import CaptchaField
from django import forms


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
