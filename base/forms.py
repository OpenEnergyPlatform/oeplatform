from django import forms
from captcha.fields import ReCaptchaField


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
    captcha = ReCaptchaField()
