"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The component catalogue at /styleguide/ (#2636, spec #2632).

Every house component has a catalogue entry: one template,
``base/templates/styleguide/entries/<name>.html``, which the page renders and
also shows as source, so the example and the snippet a contributor copies are
the same file. An entry starts with a one-line when-to-use note,
``{# use: ... #}``; a file whose name starts with ``_`` is a helper an entry
includes, not an entry. For a component that is an include, the entry is the
``{% include %}`` call with example arguments.

A house component is exactly one that lives in one of two places: a theme
partial in ``theming/scss/components/`` or an include in
``base/templates/components/``. ``catalogue_problems`` (run by
``manage.py check_catalogue`` in the catalogue workflow, deliberately not in the
test suite) fails for one without an entry of the same name.

On top of the page sits the token table: every design token, with a swatch and
the value the page computes for it, so an instance sees its own values.
``?tokens=bootstrap`` loads ``styleguide/stock_tokens.css`` after the theme,
setting every token in ``TOKENS`` to Bootstrap 5.2's stock value. Whatever
still looks like OEP then paints a literal no token controls, which is what the
literal scan (``theming/literal_scan.mjs``) fails on.
"""  # noqa: 501

import re
from dataclasses import dataclass
from pathlib import Path

from django.template.loader import render_to_string
from django.views.generic import TemplateView

REPOSITORY = Path(__file__).resolve().parent.parent
COMPONENT_PARTIALS = REPOSITORY / "theming" / "scss" / "components"
COMPONENT_INCLUDES = REPOSITORY / "base" / "templates" / "components"
ENTRIES = REPOSITORY / "base" / "templates" / "styleguide" / "entries"
COMPILED_THEME = REPOSITORY / "base" / "static" / "css" / "bootstrap.min.css"
STOCK_TOKENS = REPOSITORY / "base" / "static" / "styleguide" / "stock_tokens.css"

# The first line of an entry: {# use: <when to use it> #}
NOTE = re.compile(r"\A\{#\s*use:\s*(?P<note>[^\n]*?)\s*#\}[ \t]*\n")
# A custom property declared in a :root rule of a compiled stylesheet.
ROOT_RULE = re.compile(r":root\s*\{(?P<body>[^}]*)\}")
DECLARED = re.compile(r"(--[\w-]+)\s*:")


@dataclass(frozen=True)
class Token:
    name: str
    # How the table draws its swatch: colour, rgb (an -rgb twin), radius,
    # shadow, font, size, weight, width, motion.
    kind: str
    role: str


# Every design token, in the order of the spec's token table. The defaults live
# in theming/_variables.scss; this is the list the catalogue shows and the list
# theming/stock_tokens.scss resets for ?tokens=bootstrap.
TOKENS = (
    Token("--bs-primary", "colour", "primary action, links, brand"),
    Token("--bs-primary-rgb", "rgb", "the same colour, for Bootstrap's utilities"),
    Token("--bs-secondary", "colour", "secondary (outline) actions"),
    Token("--bs-secondary-rgb", "rgb", "the same colour, for Bootstrap's utilities"),
    Token("--bs-body-color", "colour", "text"),
    Token("--bs-body-color-rgb", "rgb", "the same colour, for Bootstrap's utilities"),
    Token("--oep-text-muted", "colour", "secondary text"),
    Token("--oep-heading-color", "colour", "platform headings"),
    Token("--bs-border-color", "colour", "borders, dividers"),
    Token("--oep-border-strong", "colour", "field borders"),
    Token("--oep-surface", "colour", "cards, overlays"),
    Token(
        "--oep-surface-subtle", "colour", "light bands, the header band, table heads"
    ),
    Token("--oep-surface-strong", "colour", "blue bands (hero, academy, footer)"),
    Token("--oep-surface-hover", "colour", "hover tint (the navbar dropdown's)"),
    Token("--oep-on-strong", "colour", "text on blue bands"),
    Token("--oep-on-strong-muted", "colour", "muted text on blue bands"),
    Token("--bs-success", "colour", "status: success, never an action"),
    Token("--bs-success-rgb", "rgb", "the same colour, for Bootstrap's utilities"),
    Token("--bs-info", "colour", "status: information, never an action"),
    Token("--bs-info-rgb", "rgb", "the same colour, for Bootstrap's utilities"),
    Token("--bs-warning", "colour", "status: warning, never an action"),
    Token("--bs-warning-rgb", "rgb", "the same colour, for Bootstrap's utilities"),
    Token("--bs-danger", "colour", "status: error; destructive actions"),
    Token("--bs-danger-rgb", "rgb", "the same colour, for Bootstrap's utilities"),
    Token("--bs-border-radius", "radius", "in the page: buttons, fields, cards"),
    Token("--bs-border-radius-sm", "radius", "small buttons, badges"),
    Token("--bs-border-radius-lg", "radius", "what floats: dropdowns, dialogs"),
    Token("--bs-border-radius-pill", "radius", "tags"),
    Token("--oep-shadow-sm", "shadow", "cards"),
    Token("--oep-shadow-lg", "shadow", "overlays: dropdowns, dialogs, toasts"),
    Token("--oep-shadow-rgb", "rgb", "the tint of both shadows"),
    Token("--bs-font-sans-serif", "font", "the font (a system stack, no web font)"),
    Token("--bs-body-font-size", "size", "text"),
    Token(
        "--oep-font-size-dense",
        "size",
        "tables, badges, sidebars, buttons, fields",
    ),
    Token("--oep-heading-weight", "weight", "headings"),
    Token("--oep-measure", "width", "reading width for prose"),
    Token(
        "--oep-content-width",
        "width",
        "content column and header band; 82, 108, 132 or 160rem by screen width",
    ),
    Token("--oep-transition", "motion", "hover motion"),
)

TOKEN_MODES = {
    "theme": "This instance",
    "bootstrap": "Bootstrap 5.2 stock",
}


@dataclass(frozen=True)
class Entry:
    name: str
    note: str
    source: str
    rendered: str


def entry_files(entries=ENTRIES):
    """The entry templates by name, without the helpers (``_*.html``)."""
    return {
        path.stem: path
        for path in sorted(entries.glob("*.html"))
        if not path.name.startswith("_")
    }


def component_sources(partials=COMPONENT_PARTIALS, includes=COMPONENT_INCLUDES):
    """Every house component by name, with the files it is made of."""
    sources = {}
    for path in sorted(partials.glob("_*.scss")):
        sources.setdefault(path.stem[1:], []).append(path)
    for path in sorted(includes.glob("*.html")):
        sources.setdefault(path.stem, []).append(path)
    return sources


def split_entry(text):
    """``(note, source)`` of an entry template; the note is ``""`` without one."""
    match = NOTE.match(text)
    if not match:
        return "", text.strip()
    return match.group("note"), text[match.end() :].strip()


def root_tokens(css):
    """The custom properties a compiled stylesheet declares at ``:root``."""
    return {
        name
        for rule in ROOT_RULE.finditer(css)
        for name in DECLARED.findall(rule.group("body"))
    }


def _shown(path):
    return (
        str(path.relative_to(REPOSITORY))
        if path.is_relative_to(REPOSITORY)
        else str(path)
    )


def catalogue_problems(
    partials=COMPONENT_PARTIALS,
    includes=COMPONENT_INCLUDES,
    entries=ENTRIES,
    theme=COMPILED_THEME,
    stock=STOCK_TOKENS,
    tokens=TOKENS,
):
    """What keeps the catalogue from being complete, one sentence each."""
    problems = []
    files = entry_files(entries)
    for name, paths in component_sources(partials, includes).items():
        if name not in files:
            made_of = ", ".join(_shown(path) for path in paths)
            problems.append(
                f"{name} ({made_of}) is a house component without a catalogue "
                f"entry: add base/templates/styleguide/entries/{name}.html"
            )
    for name, path in files.items():
        if not split_entry(path.read_text())[0]:
            problems.append(
                f"the entry {name} does not start with its when-to-use note, "
                "{# use: ... #}"
            )

    names = {token.name for token in tokens}
    in_theme = root_tokens(theme.read_text())
    in_stock = root_tokens(stock.read_text())
    for name in sorted(names - in_theme):
        problems.append(f"the token {name} is not declared at :root by the theme")
    for name in sorted(names - in_stock):
        problems.append(
            f"the token {name} has no stock value in theming/stock_tokens.scss"
        )
    declared = {n for n in in_theme if n.startswith("--oep-")} | in_stock
    for name in sorted(declared - names):
        problems.append(
            f"the token {name} is missing from the catalogue's token table "
            "(TOKENS in base/styleguide.py)"
        )
    return problems


def render_entries(request, context, entries=ENTRIES):
    for name, path in entry_files(entries).items():
        note, source = split_entry(path.read_text())
        yield Entry(
            name=name,
            note=note,
            source=source,
            rendered=render_to_string(
                f"styleguide/entries/{path.name}", context, request
            ),
        )


class StyleguideView(TemplateView):
    """The catalogue: public, ``noindex``, linked from no menu.

    ``stock_tokens`` is true under ``?tokens=bootstrap``. The page then renders
    with Bootstrap's stock values and without any instance stylesheet, so the
    instance stylesheet slot (#2637) must leave the page alone when it is set.
    """

    template_name = "styleguide/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mode = self.request.GET.get("tokens")
        context["token_mode"] = mode if mode in TOKEN_MODES else "theme"
        context["token_modes"] = TOKEN_MODES
        context["stock_tokens"] = context["token_mode"] == "bootstrap"
        context["tokens"] = TOKENS
        context["entries"] = list(render_entries(self.request, context))
        return context
