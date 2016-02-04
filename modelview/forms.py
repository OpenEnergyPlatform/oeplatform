from django.forms import ModelForm
from modelview.models import Energymodel

# Create the form class.
class EnergymodelForm(ModelForm):
    class Meta:
        model = Energymodel
        fields = [f.name for f in Energymodel._meta.fields]

