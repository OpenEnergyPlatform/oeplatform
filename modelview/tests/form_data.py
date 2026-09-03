"""What a factsheet edit form actually submits, derived from the form itself.

Separate from `corpus.py`, which seeds rows in the database: this module knows
nothing about the database and everything about the widgets -- how
`array_snippet.html` names its inputs, that an unchecked checkbox is absent
rather than `off`, that the tag widget posts raw primary keys.

A factsheet carries ~190 fields, so the values are derived from the form
rather than listed. A hand-written list would drift the first time a field was
added, and drift is precisely what the round-trip test exists to catch.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from datetime import date
from typing import Any

from django.contrib.postgres.forms.array import SimpleArrayField
from django.forms import BooleanField, DateField, FileField

from modelview.helper import getClasses


def form_values(sheettype: str, model_name: str) -> dict:
    """A distinctive, valid value for every editable field of a factsheet.

    Booleans alternate rather than being all-true or all-false: an unchecked
    checkbox is simply absent from a submit, so a corpus of one value only
    could not tell "dropped every checkbox" from "checked every checkbox".

    `tags` is left out -- a caller that wants tags passes raw pks alongside,
    the way the widget does -- and so is the one file field, which cannot be
    round-tripped through a plain POST body.
    """
    _, form_cls = getClasses(sheettype)
    if form_cls is None:
        raise ValueError("unknown sheettype: %r" % (sheettype,))

    values: dict[str, Any] = {}
    for index, (name, form_field) in enumerate(sorted(form_cls().fields.items())):
        if name == "tags" or isinstance(form_field, FileField):
            continue
        values[name] = _sample_value(name, form_field, index)

    values["model_name"] = model_name
    return values


def as_post_data(values: dict) -> dict:
    """Serialise `form_values` the way the edit form's widgets do.

    Three contracts live here, all of them load-bearing for the write path: an
    array field posts one input per entry under `<name>_<i>`, counting from 1
    because `array_snippet.html` starts its counter there and there is no bare
    `<name>` key in a real submit; an unchecked checkbox is *absent*, not
    `off`; everything else posts its string form.
    """
    data: dict[str, Any] = {}
    for name, value in values.items():
        if isinstance(value, list):
            for offset, entry in enumerate(value):
                data["%s_%d" % (name, offset + 1)] = entry
        elif isinstance(value, bool):
            if value:
                data[name] = "on"
        elif value is None:
            data[name] = ""
        else:
            data[name] = str(value)
    return data


def _sample_value(name: str, form_field, index: int):
    if isinstance(form_field, SimpleArrayField):
        base = "%s-%%d@example.org" if name == "contact_email" else "%s entry %%d"
        return [(base % name) % i for i in range(3)]
    if isinstance(form_field, BooleanField):
        return index % 2 == 0
    if isinstance(form_field, DateField):
        return date(2026, 1, 15)
    choices = list(getattr(form_field, "choices", []) or [])
    if choices:
        # Skip the empty "---------" entry Django prepends to an optional
        # select; posting it would mean "not answered".
        for value, _label in choices:
            if value:
                return value
    max_length = getattr(form_field, "max_length", None) or 100
    return ("%s value" % name)[:max_length]
