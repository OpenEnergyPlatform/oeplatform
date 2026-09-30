"""The Model/Framework Factsheet list page's row payload, built in the view.

This used to be a JS object literal assembled in `modellist.html`, and its
`model_name` and `tags` keys sat *inside* the loop over the view-property
groups -- so every row emitted them once per group: seven times for a model
factsheet, four for a framework. At production's shape that is 85,092 tag
objects for 12,156 attachments and 2,135 duplicate `model_name` lines, and
because duplicate keys in a JS object literal silently overwrite, the page
looked correct throughout. **A dict cannot have that bug**, which is the
reason this module exists rather than a two-line template hoist that would
also have hit the query target.

The other half of the cost was the missing prefetch: `model.tags.all` inside
that loop meant `7 x N` queries with nothing caching them (2,138 at
production's shape). One `prefetch_related("tags")` in the view feeds the
whole payload, and the list page issues 3 queries whatever N is. Locally that
buys no wall time -- a query over a unix socket is ~0.1 ms -- which is exactly
why the query count is a bound in its own right and not a proxy for seconds.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

from django.utils.html import escape, format_html

# A `simple_tag` decorator returns the function it decorated, so this is the
# same pure helper the sidebar's template tag calls -- not a second
# implementation of the contrast rule that could drift away from it.
from dataedit.templatetags.dataedit.taghandler import readable_text_color

#: Cell values are truncated to this many words, as they have been since the
#: table shipped. It costs nothing (3.43 -> 3.28 MB at production's shape) and
#: dropping it would silently change what every cell displays.
MAX_WORDS = 12


def leaf_fields(view_props):
    """Every field name the view properties name, flat and in render order.

    The view properties are three levels deep -- group, labelled subgroup,
    field names -- and only the leaves are model fields. 171 of them for a
    model factsheet, 41 for a framework.
    """
    return [
        field
        for group in view_props.values()
        for names in group.values()
        for field in names
    ]


def initial_fields(view_props, default_columns):
    """The leaf fields the *first* payload carries: the default columns.

    `model_name` and `tags` are in `default_columns` too but are not leaf
    fields -- the builder always emits them -- so they are filtered out here
    rather than special-cased twice.

    Six of 171 for a model factsheet, three of 41 for a framework. The rest
    arrive from the full-payload endpoint on the first column toggle or the
    first search keystroke, because shipping all of them costs 20.1 MB to
    display eight columns.
    """
    return [field for field in leaf_fields(view_props) if field in default_columns]


def build_list_payload(queryset, fields):
    """One row dict per factsheet in `queryset`, carrying `fields`.

    Two preconditions on `queryset`: it carries `prefetch_related("tags")`,
    or this is an N+1 again; and it is not deferred, because the field values
    are read from each instance's `__dict__` and a `.only()`/`.defer()` row
    would raise `KeyError` for whatever it left behind.

    `fields` is the explicit list of model field names to include, which is
    what lets the same builder serve both the page-sized initial payload and
    the lazy full-payload endpoint.
    """
    tag_payloads = {}
    return [_row(sheet, fields, tag_payloads) for sheet in queryset]


def _row(sheet, fields, tag_payloads):
    row = {
        # The table renders this cell as HTML, so the name is escaped here.
        # A relative href, unchanged: the list lives at `<sheettype>s/` and
        # the detail page at `<sheettype>s/<pk>/`.
        "model_name": format_html('<a href="{}">{}</a>', sheet.id, sheet.model_name),
        # The FULL array, never the five the renderer displays: the
        # client-side filter iterates a row's whole tag list to decide whether
        # the row matches the active selection.
        "tags": [_tag(tag, tag_payloads) for tag in sheet.tags.all()],
    }
    for name in fields:
        # `__dict__`, not `getattr`: it is the raw column value, which is what
        # the template read and what JSON can carry. `getattr` would hand back
        # an `ImageFieldFile` for `logo` and fail to serialise.
        row[name] = _cell(sheet.__dict__[name])
    return row


def _tag(tag, tag_payloads):
    """One tag's display data, built once per tag rather than once per edge.

    The same tag appears on many rows -- and on all of them for a factsheet
    the old editor corrupted -- so the contrast calculation is memoised. The
    dicts are shared between rows deliberately; nothing mutates them.
    """
    payload = tag_payloads.get(tag.pk)
    if payload is None:
        payload = tag_payloads[tag.pk] = {
            "pk": tag.pk,
            "name": tag.name,
            "color_hex": tag.color_hex,
            "textcolor_hex": readable_text_color(tag.color_hex),
        }
    return payload


def _cell(value):
    """One cell value: truncated, newline-free and HTML-escaped.

    Escaped because the table writes every cell through `innerHTML`, so a
    field containing `<img src=x onerror=...>` would otherwise execute -- and
    any logged-in account can edit any factsheet. `json_script` protects the
    *transport* (nothing can close the script element); this protects the
    *cell*. The old template filter did both jobs at once, and only its
    JS-literal half is obsolete.

    Non-strings -- numbers, booleans, `None`, dates -- pass through for
    `DjangoJSONEncoder` to render; array fields are escaped entry by entry,
    as they were before.
    """
    if isinstance(value, str):
        parts = value.split(" ")
        if len(parts) > MAX_WORDS:
            parts = parts[:MAX_WORDS] + ["..."]
        text = " ".join(parts).replace("\n", "").replace("\r", "")
        return escape(text)
    if isinstance(value, list):
        return [_cell(entry) for entry in value]
    return value
