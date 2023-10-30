from django.forms import ModelForm

from modelview.models import Energyframework, Energymodel


# Create the form class.
class EnergymodelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EnergymodelForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            f = [not f.null for f in Energymodel._meta.fields if f.name == key][0]
            self.fields[key].required = (
                f and self.fields[key].widget.__class__.__name__ != "CheckboxInput"
            )

    class Meta:
        model = Energymodel
        exclude = []


class EnergyframeworkForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EnergyframeworkForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            f = [not f.null for f in Energyframework._meta.fields if f.name == key][0]
            self.fields[key].required = (
                f and self.fields[key].widget.__class__.__name__ != "CheckboxInput"
            )
            if "help_text" in self.fields[key].__dict__:
                self.fields[key].help_text = self.fields[key].help_text.replace(
                    "model", "framework"
                )
            if "label" in self.fields[key].__dict__:
                if self.fields[key].label == "Model usage":
                    self.fields[key].label = "Framework usage"

    class Meta:
        model = Energyframework
        exclude = []
