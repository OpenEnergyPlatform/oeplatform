from django.forms import ModelForm
from modelview.models import Energymodel, Energyframework, Energyscenario

# Create the form class.
class EnergymodelForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(EnergymodelForm, self).__init__(*args, **kwargs)
        print([self.fields[f].required for f in self.fields])
        for key in self.fields:
            f = [not f.null for f in Energymodel._meta.fields if f.name==key][0]
            self.fields[key].required = f and self.fields[key].widget.__class__.__name__ != "CheckboxInput"
        
    class Meta:
        model = Energymodel
        exclude = []
        

class EnergyframeworkForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(EnergyframeworkForm, self).__init__(*args, **kwargs)
        print([self.fields[f].required for f in self.fields])
        for key in self.fields:
            f = [not f.null for f in Energyframework._meta.fields if f.name==key][0]
            self.fields[key].required = f and self.fields[key].widget.__class__.__name__ != "CheckboxInput"
        
    class Meta:
        model = Energyframework
        exclude = []


class EnergyscenarioForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(EnergyscenarioForm, self).__init__(*args, **kwargs)
        print([self.fields[f].required for f in self.fields])
        for key in self.fields:
            f = [not f.null for f in Energyscenario._meta.fields if f.name==key][0]
            self.fields[key].required = f and self.fields[key].widget.__class__.__name__ != "CheckboxInput"
        
    class Meta:
        model = Energyscenario
        exclude = []


