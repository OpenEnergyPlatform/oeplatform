from django import forms
from .models import Tutorial


class TutorialForm(forms.ModelForm):

    class Meta:
        model = Tutorial
        fields = ('category', 'title', 'markdown', 'media_src', 'level',
                  'language', 'medium', 'creator', 'email_contact', 'github')
