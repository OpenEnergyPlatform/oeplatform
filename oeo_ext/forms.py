from django import forms

from oeo_ext.oeo_extended_store.connection import oeo_owl


class UnitName(forms.CharField):
    def validate(self, value):
        """Check if value consists only of valid emails."""
        # Use the parent's handling of required fields, etc.
        super().validate(value)

        in_oeo = oeo_owl.search_one(label=value)

        if not in_oeo:
            raise forms.ValidationError(
                "The value was not found in the oeo."
                "Please use a value from the suggestion."
            )


class UnitEntryForm(forms.Form):
    position = forms.IntegerField(
        min_value=1, error_messages={"min_value": "Position must be a positive integer"}
    )

    unitName = UnitName(
        max_length=255, error_messages={"required": "This field cannot be empty"}
    )
    unitType = forms.CharField(
        max_length=255, error_messages={"required": "This field cannot be empty"}
    )


class ComposedUnitFormWrapper(forms.Form):
    definition = forms.CharField(
        widget=forms.Textarea(), required=False, max_length=255
    )
    unitLabel = forms.CharField(required=False, max_length=255)
