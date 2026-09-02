"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 quentinpeyras <https://github.com/quentinpeyras>
SPDX-FileCopyrightText: 2025 Lara Christmann <https://github.com/solar-c> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Lara Christmann <https://github.com/solar-c> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.forms import ModelForm
from django.utils.functional import cached_property

from modelview.models import Energyframework, Energymodel


class FactsheetTagsMixin:
    """The tag selection this form carries, as a set of raw primary keys.

    `tag_selector.html` needs a membership test per rendered checkbox, and the
    only safe shape for that is a small in-memory collection. Testing `in`
    against a `QuerySet` is what made the list page quadratic (Django defines
    no `QuerySet.__contains__`, so `in` falls back to iterating the whole
    result cache); the same mistake here would scan the vocabulary once per
    checkbox.

    Reading it off the *bound* form is what makes a failed submit come back
    with the user's selection intact -- and what makes an unbound edit form
    show that factsheet's own tags and nothing else.
    """

    @cached_property
    def selected_tag_pks(self) -> set:
        return {str(pk) for pk in (self["tags"].value() or [])}


# Create the form class.
class EnergymodelForm(FactsheetTagsMixin, ModelForm):
    def __init__(self, *args, **kwargs):
        super(EnergymodelForm, self).__init__(*args, **kwargs)
        # set some as required
        for key in self.fields:
            if key == "tags":
                self.fields[key].required = False
            else:
                f = [not f.null for f in Energymodel._meta.fields if f.name == key][0]
                cls_name = self.fields[key].widget.__class__.__name__  # type: ignore
                self.fields[key].required = f and cls_name != "CheckboxInput"

    class Meta:
        model = Energymodel
        exclude = []


class EnergyframeworkForm(FactsheetTagsMixin, ModelForm):
    def __init__(self, *args, **kwargs):
        super(EnergyframeworkForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            if key == "tags":
                self.fields[key].required = False
            else:
                f = [not f.null for f in Energyframework._meta.fields if f.name == key][
                    0
                ]
                cls_name = self.fields[key].widget.__class__.__name__  # type: ignore
                self.fields[key].required = f and cls_name != "CheckboxInput"
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
