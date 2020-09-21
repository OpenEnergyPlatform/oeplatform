from django.forms import Form
from django_jsonforms.forms import JSONSchemaField




options = {
        'theme': 'bootstrap4',
        'disable_collapse': True,
        'disable_properties': True,
        'compact': True,
        'disable_array_reorder': True
}
class CreatorForm(Form):
    Meta_v_1_4_0 = JSONSchemaField(schema='oem_v_1_4_0.json', options=options)