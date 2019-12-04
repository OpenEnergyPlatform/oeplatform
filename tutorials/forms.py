from django import forms
from .models import Tutorial


class TutorialForm(forms.ModelForm):
    # ToDO: Set required fields??

    class Meta:
        model = Tutorial
        fields = ('title', 'html', 'markdown')