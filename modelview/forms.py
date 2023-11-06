from django.forms import ModelForm

from modelview.models import Energyframework, Energymodel, Energyscenario, Energystudy


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


class EnergystudyForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EnergystudyForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            f = [not f.null for f in Energystudy._meta.fields if f.name == key][0]
            self.fields[key].required = (
                f and self.fields[key].widget.__class__.__name__ != "CheckboxInput"
            )

    class Meta:
        model = Energystudy
        exclude = []


class EnergyscenarioForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EnergyscenarioForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            f = [not f.null for f in Energyscenario._meta.fields if f.name == key][0]
            self.fields[key].required = (
                f and self.fields[key].widget.__class__.__name__ != "CheckboxInput"
            )

    class Meta:
        model = Energyscenario
        exclude = []

    def clean(self):
        cleaned_data = super(EnergyscenarioForm, self).clean()
        for name in [
            "energy_saving",
            "potential_energy_savings",
            "emission_reductions",
            "share_RE_power",
            "share_RE_heat",
            "share_RE_mobility",
            "share_RE_total",
        ]:
            name_kind = cleaned_data[name + "_kind"]
            name_amount = cleaned_data[name + "_amount"]
            if name_kind != "not estimated" and name_amount is None:
                self.add_error(name + "_amount", "This field is required")
            name_year = cleaned_data[name + "_year"]
            if name_kind != "not estimated" and name_year is None:
                self.add_error(name + "_year", "This field is required")

        return cleaned_data
