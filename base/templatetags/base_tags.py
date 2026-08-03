"""
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from pathlib import Path, PurePosixPath

import markdown2
from django import template
from django.contrib.staticfiles import finders
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="addclass")
def addclass(field, css):
    return field.as_widget(attrs={"class": css})


def _is_safe_static_path(filename):
    path = PurePosixPath(filename)
    return not path.is_absolute() and ".." not in path.parts


_RELEASE_FILE_PATTERN = re.compile(r"^(\d+)_(\d+)_(\d+)\.md$")

_CHANGELOG_DIRECTORY = Path(__file__).resolve().parents[2] / "versions" / "changelogs"


def _get_release_version(path):
    """Read the version from a filename such as 1_8_0.md."""
    match = _RELEASE_FILE_PATTERN.fullmatch(path.name)

    if match is None:
        return None

    return tuple(int(number) for number in match.groups())


def _find_latest_release_changelog():
    """Find the newest published changelog."""
    release_files = []

    for path in _CHANGELOG_DIRECTORY.glob("*.md"):
        version = _get_release_version(path)

        if version is not None:
            release_files.append((version, path))

    if not release_files:
        return None

    return max(release_files, key=lambda item: item[0])[1]


def _extract_startpage_highlights(markdown_content):
    """Read only the Startpage Highlights section."""
    pattern = re.compile(
        r"^## Startpage Highlights\s*$\n" r"(?P<content>.*?)(?=^##\s|\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )

    match = pattern.search(markdown_content)

    if match is None:
        return ""

    return match.group("content").strip()


@register.simple_tag
def render_latest_release_highlights():
    """Render highlights from the newest published changelog."""
    latest_changelog = _find_latest_release_changelog()

    if latest_changelog is None:
        return ""

    try:
        markdown_content = latest_changelog.read_text(encoding="utf-8")
    except OSError:
        return ""

    highlights = _extract_startpage_highlights(markdown_content)

    if not highlights:
        return ""

    markdowner = markdown2.Markdown()
    return mark_safe(markdowner.convert(highlights))


@register.simple_tag
def render_markdown(filename):
    """Find a markdown file in staticfiles and render it as HTML.

    The staticfiles lookup allows markdown content to live in any Django app's
    static directory. The fallback keeps the old ``base/static/content`` lookup
    behaviour for existing callers that pass only a filename.
    """
    if not _is_safe_static_path(filename):
        return ""

    md_path = finders.find(filename)
    if not md_path:
        md_path = (
            Path(__file__).resolve().parent.parent / "static" / "content" / filename
        )

    try:
        content = Path(md_path).read_text(encoding="utf-8")
    except OSError:
        return ""

    markdowner = markdown2.Markdown()
    return mark_safe(markdowner.convert(content))
