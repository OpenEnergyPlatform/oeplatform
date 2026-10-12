"""The page lint (spec #2632, "a drift guard beyond the catalogue").

Every action on a restyled page carries one of the four button roles on
itself, so that a button added later with Bootstrap's defaults, or with no
class at all, is caught instead of drifting the page back. `lint` reads one
rendered page and answers what on it breaks the rule:

- a `<button>`, or an `<input>` of type submit or button, without `btn` and a
  role, unless it is a house component's own control (a dialog's close
  button, a tab, a tag's remove button, ...);
- any other element styled as a button (`btn`, a link most often) without a
  role, except the `<label>` of a segmented control's option;
- any element styled as a button in a status colour (green, cyan, yellow,
  black or light grey), which is never an action's colour;
- a native `confirm(` or `alert(` in an inline script or event handler.

It reads the page's own content, `#main-content`, for the first three: the
navbar is the shell's, and the user menu (#2644) moves its last coloured
buttons. A page without `#main-content` is refused rather than passed. An
htmx fragment has no shell, so `fragment=True` reads all of it. Inline
scripts are read wherever they are on the page.

`hx-confirm` is not a native dialog: templates keep the attribute, and the
shell's confirm dialog (#2643, `base/static/base/dialogs.js`) answers every
one of them in place of htmx's own `confirm()`. A plain button asks the same
dialog with `data-confirm`.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from html.parser import HTMLParser

from modelview.tests.html import element_markup

#: The four roles (spec #2632, "button"), as classes. `btn-outline-secondary`
#: is Bootstrap's own name for the secondary role and looks the same;
#: `btn-on-strong` is the light button for a blue band.
ROLES = frozenset(
    {
        "btn-primary",
        "btn-secondary",
        "btn-outline-secondary",
        "btn-danger",
        "btn-outline-danger",
        "btn-link",
        "btn-on-strong",
    }
)

#: Buttons that belong to a house component rather than carrying a role of
#: their own: a dialog's close button, the navbar's toggler, a tab, a menu
#: item, a tag's remove button. A component ticket that adds a control of its
#: own (the section card's header, field help) adds its class here.
HOUSE_CONTROLS = frozenset(
    {"btn-close", "navbar-toggler", "nav-link", "dropdown-item", "tag__remove"}
)

#: Bootstrap's status colours, which are never a button's (an outline in one
#: of them neither).
STATUS_COLOURS = ("success", "info", "dark", "warning", "light")


def status_button(colours=STATUS_COLOURS):
    """The class of a button in one of `colours`, solid or outlined."""
    return re.compile(r"^btn-(?:outline-)?(?:%s)$" % "|".join(colours))


STATUS_BUTTON = status_button()

#: A call of the browser's own dialog: `confirm(`, `alert(`, or the same on
#: `window.`. A method of that name on anything else (`dialog.confirm(`) or a
#: longer name (`showAlert(`) is not one.
NATIVE_DIALOG = re.compile(r"(?:(?<![\w$.])|\bwindow\.)(?:confirm|alert)\s*\(")


class _Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []  # (tag, attrs)
        self.scripts = []
        self._script = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if tag == "script" and not attrs.get("src"):
            self._script = []

    def handle_endtag(self, tag):
        if tag == "script" and self._script is not None:
            self.scripts.append("".join(self._script))
            self._script = None

    def handle_data(self, data):
        if self._script is not None:
            self._script.append(data)


def _parse(markup):
    page = _Page()
    page.feed(markup)
    return page


def _describe(tag, attrs):
    shown = " ".join(
        f'{name}="{attrs[name]}"'
        for name in ("id", "class", "type", "value")
        if attrs.get(name)
    )
    return f"<{tag} {shown}>" if shown else f"<{tag}>"


def is_action(tag, attrs):
    """A `<button>`, or an `<input>` a click submits or acts on."""
    if tag == "button":
        return True
    return tag == "input" and (attrs.get("type") or "").lower() in (
        "submit",
        "button",
    )


def lint(html: str, fragment: bool = False) -> list[str]:
    """Every way the rendered page `html` breaks the button rule, one line
    each; an empty list when it keeps it. `fragment`: `html` is an htmx
    fragment, read whole, rather than a page with a shell."""
    problems = []
    content = html if fragment else element_markup(html, "main-content")
    if not content:
        raise ValueError("no #main-content: not a page, or a shell without one")
    for tag, attrs in _parse(content).elements:
        classes = set((attrs.get("class") or "").split())
        statuses = sorted(c for c in classes if STATUS_BUTTON.match(c))
        for status in statuses:
            problems.append(
                f"{_describe(tag, attrs)}: {status} is a status colour, not a role"
            )
        if statuses or classes & HOUSE_CONTROLS:
            continue
        # A label styled as a button is an option of a segmented control
        # (Bootstrap's `btn-check`), which fills when it is the one chosen:
        # a choice, not an action.
        if tag == "label" or not (is_action(tag, attrs) or "btn" in classes):
            continue
        if "btn" not in classes or not classes & ROLES:
            problems.append(f"{_describe(tag, attrs)}: no btn and role on itself")

    page = _parse(html)
    handlers = (
        value or ""
        for _, attrs in page.elements
        for name, value in attrs.items()
        if name.startswith("on")
    )
    for code in (*page.scripts, *handlers):
        for match in NATIVE_DIALOG.finditer(code):
            start = max(match.start() - 30, 0)
            problems.append(
                "a native dialog: …" + " ".join(code[start : match.end() + 30].split())
            )
    return problems
