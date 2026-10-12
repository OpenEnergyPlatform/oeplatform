"""The instance theming contract (#2637, spec #2632): a third-party instance
restyles the platform with two settings and no fork.

``INSTANCE_STYLESHEETS`` links the instance's stylesheets last in every shell's
head, so its token values win; ``INSTANCE_TEMPLATE_DIRS`` is searched first, so
its brand (``brand/``) and legal pages replace the platform's. Asserted through
the pages a browser receives: which stylesheets a head links and in which
order, what the title, the navbar and the legal pages say. Never pixels; the
homepage comparison (benchmarks/homepage/compare.mjs) checks those, outside the
suite. The deploy sequence with an instance's files (collectstatic, compress, a
page) is in test_static_files.py.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, override_settings

from base.checks import check_instance_stylesheets, check_instance_template_dirs
from base.styleguide import TOKENS
from dataedit.tests.test_dataset_sidebar import SidebarFixture

SHELLS = Path(settings.BASE_DIR) / "base" / "templates" / "base"
SHELL_NAMES = (
    "base.html",
    "base-full.html",
    "base-profile.html",
    "base-sidebar.html",
    "base-wide-react.html",
)
NAVBAR = "_header.html"
THEMING_DOCS = (
    Path(settings.BASE_DIR) / "docs" / "installation" / "guides" / "instance-theming.md"
)

THEME = "instance/theme.css"
PRINT = "instance/print.css"

STYLESHEET = re.compile(r"<link\b[^>]*\brel=\"stylesheet\"[^>]*>")
HREF = re.compile(r'\bhref="([^"]*)"')


def head(html):
    return html[html.index("<head>") : html.index("</head>")]


def stylesheets(html):
    """The addresses of the stylesheets a page's head links, in order."""
    return [HREF.search(link).group(1) for link in STYLESHEET.findall(head(html))]


def instance_files(directory):
    """An instance's static directory with two stylesheets in it."""
    static = Path(directory) / "static"
    (static / "instance").mkdir(parents=True)
    for name in (THEME, PRINT):
        (static / name).write_text(":root { --bs-primary: #7a1f5d; }\n")
    return static


class InstanceStaticFiles:
    """A temporary STATICFILES_DIRS holding the instance's stylesheets, so the
    suite's storage, which refuses a name no finder has, accepts them."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(directory.cleanup)
        cls.instance_static = instance_files(directory.name)

    def instance(self, *paths):
        return override_settings(
            STATICFILES_DIRS=[self.instance_static], INSTANCE_STYLESHEETS=list(paths)
        )


class ShellPagesTestCase(InstanceStaticFiles, SidebarFixture):
    """One page of each of the five shells, with the catalogue beside them."""

    def pages(self):
        return (
            ("base.html", "base:home", None, False),
            ("base-full.html", "base:about", None, False),
            ("base-profile.html", "login:settings", {"user_id": self.user.pk}, True),
            ("base-sidebar.html", "dataedit:view", {"table": self.table_name}, False),
            ("base-wide-react.html", "factsheet:factsheets_index", None, False),
        )

    def page(self, view_name, kwargs=None, logged_in=False, query=None):
        response = self.get(view_name, kwargs=kwargs, logged_in=logged_in, query=query)
        return response.content.decode()


class InstanceStylesheetTest(ShellPagesTestCase):
    @override_settings(INSTANCE_STYLESHEETS=[])
    def test_unset_a_page_links_no_instance_stylesheet(self):
        for shell, view_name, kwargs, logged_in in self.pages():
            with self.subTest(shell=shell):
                links = stylesheets(self.page(view_name, kwargs, logged_in))
                self.assertTrue(links, "the platform's own stylesheets")
                self.assertFalse([link for link in links if "instance/" in link])

    def test_set_every_shell_links_it_after_every_platform_stylesheet(self):
        with self.instance(THEME):
            for shell, view_name, kwargs, logged_in in self.pages():
                with self.subTest(shell=shell):
                    links = stylesheets(self.page(view_name, kwargs, logged_in))
                    self.assertGreater(len(links), 1)
                    self.assertEqual(links[-1], f"/static/{THEME}")
                    self.assertEqual(links.count(f"/static/{THEME}"), 1)

    def test_it_follows_a_page_s_own_stylesheet(self):
        # The catalogue links styleguide.css in its own head block, and the
        # instance's values must win over a page's as over the theme's.
        with self.instance(THEME):
            links = stylesheets(self.page("base:styleguide"))
        self.assertEqual(
            links[-2:], ["/static/styleguide/styleguide.css", f"/static/{THEME}"]
        )

    def test_several_are_linked_in_the_order_given(self):
        with self.instance(THEME, PRINT):
            links = stylesheets(self.page("base:about"))
        self.assertEqual(links[-2:], [f"/static/{THEME}", f"/static/{PRINT}"])


class CatalogueTest(ShellPagesTestCase):
    def test_the_catalogue_shows_the_instance_s_values(self):
        with self.instance(THEME):
            links = stylesheets(self.page("base:styleguide"))
        self.assertEqual(links[-1], f"/static/{THEME}")

    def test_under_stock_tokens_the_catalogue_leaves_it_out(self):
        with self.instance(THEME):
            links = stylesheets(
                self.page("base:styleguide", query={"tokens": "bootstrap"})
            )
        self.assertNotIn(f"/static/{THEME}", links)
        self.assertTrue(links[-1].endswith("styleguide/stock_tokens.css"))


class InstanceTemplatesTest(ShellPagesTestCase):
    """A directory in INSTANCE_TEMPLATE_DIRS, holding the documented override
    surface: the brand and the two legal pages."""

    NAME = "Example Grid Platform"
    PREFIX = "EGP"
    LOGO = '<img class="example-logo" alt="{{ alt }}" src="/example.svg" />'
    PRIVACY = (
        '{% extends "base/base.html" %}'
        "{% block main-content-body %}<h1>Example privacy</h1>{% endblock %}"
    )
    TERMS = (
        '{% extends "base/base.html" %}'
        "{% block main-content-body %}<h1>Example terms</h1>{% endblock %}"
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(directory.cleanup)
        templates = Path(directory.name)
        for name, text in {
            "brand/name.html": f"{cls.NAME}\n",
            "brand/title_prefix.html": f"{cls.PREFIX}\n",
            "brand/logo.html": f"{cls.LOGO}\n",
            "base/privacy_policy.html": cls.PRIVACY,
            "base/terms_of_use.html": cls.TERMS,
        }.items():
            (templates / name).parent.mkdir(parents=True, exist_ok=True)
            (templates / name).write_text(text)
        cls.templates = str(templates)

    def instance_templates(self):
        # What settings.py makes of INSTANCE_TEMPLATE_DIRS (see
        # test_static_files.py for the settings themselves).
        return override_settings(
            TEMPLATES=[{**settings.TEMPLATES[0], "DIRS": [self.templates]}]
        )

    def title(self, html):
        return " ".join(re.search(r"<title>(.*?)</title>", html, re.S).group(1).split())

    def test_the_brand_s_name_and_logo_replace_the_platform_s(self):
        with self.instance_templates():
            html = self.page("base:home")
        self.assertIn(
            f'<img class="example-logo" alt="{self.NAME} home" src="/example.svg" />',
            html,
        )
        self.assertIn(f'<p class="index-footer-brand-name">{self.NAME}</p>', html)
        self.assertNotIn("Open Energy Platform", html.split("<main")[0])
        self.assertNotIn("OpenEnergyFamily_Logo", html)

    def test_the_name_is_text_escaped_alike_in_an_attribute_and_in_text(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "brand").mkdir()
            (Path(directory) / "brand" / "name.html").write_text("R&D <Grid>\n")
            templates = [{**settings.TEMPLATES[0], "DIRS": [directory]}]
            with override_settings(TEMPLATES=templates):
                html = self.page("base:home")
        self.assertIn('alt="R&amp;D &lt;Grid&gt; home"', html)
        self.assertIn(
            '<p class="index-footer-brand-name">R&amp;D &lt;Grid&gt;</p>', html
        )

    def test_every_shell_s_title_starts_with_the_prefix(self):
        with self.instance_templates():
            for shell, view_name, kwargs, logged_in in self.pages():
                with self.subTest(shell=shell):
                    title = self.title(self.page(view_name, kwargs, logged_in))
                    self.assertTrue(title.startswith(self.PREFIX), title)

    def test_the_legal_pages_replace_the_platform_s(self):
        with self.instance_templates():
            privacy = self.page("base:legal-privacy-policy")
            terms = self.page("base:legal-tou")
        self.assertIn("<h1>Example privacy</h1>", privacy)
        self.assertNotIn("Privacy policy</h1>", privacy)
        self.assertIn("<h1>Example terms</h1>", terms)

    def test_without_them_the_platform_s_brand_shows(self):
        with override_settings(TEMPLATES=[{**settings.TEMPLATES[0], "DIRS": []}]):
            html = self.page("base:home")
        self.assertEqual(self.title(html).split()[0], "OEP")
        self.assertIn('alt="Open Energy Platform home"', html)


class ShellTemplatesTest(SimpleTestCase):
    """The shells as templates: one shared head, the slot last, and no brand
    written into a shell or the navbar."""

    BRAND_LITERALS = re.compile(
        r"Open Energy Platform|\bOEP\b|OpenEnergyFamily_Logo|OEP_logo"
    )

    def source(self, name):
        return (SHELLS / name).read_text()

    def test_every_shell_shares_one_head(self):
        for name in SHELL_NAMES:
            with self.subTest(shell=name):
                shell_head = head(self.source(name))
                self.assertEqual(shell_head.count('{% include "base/_head.html" %}'), 1)
                self.assertNotIn("{% compress", shell_head)
                self.assertNotIn("bootstrap.min.css", shell_head)

    def test_the_slot_is_the_last_thing_in_every_head(self):
        for name in SHELL_NAMES:
            with self.subTest(shell=name):
                self.assertTrue(
                    head(self.source(name))
                    .rstrip()
                    .endswith('{% include "base/_instance_stylesheets.html" %}')
                )

    def test_no_shell_or_navbar_writes_the_brand(self):
        for name in (*SHELL_NAMES, NAVBAR):
            with self.subTest(template=name):
                self.assertEqual(self.BRAND_LITERALS.findall(self.source(name)), [])


@override_settings(INSTANCE_STYLESHEETS=[], INSTANCE_TEMPLATE_DIRS=[])
class ChecksTest(InstanceStaticFiles, SimpleTestCase):
    def test_unset_nothing_is_reported(self):
        self.assertEqual(check_instance_stylesheets(None), [])
        self.assertEqual(check_instance_template_dirs(None), [])

    def test_a_stylesheet_no_finder_has_is_an_error(self):
        # With DEBUG off the static storage refuses the name, and every page
        # links it.
        with self.instance(THEME, "instance/missing.css"):
            errors = check_instance_stylesheets(None)
        self.assertEqual([error.id for error in errors], ["base.E001"])
        self.assertIn("instance/missing.css", errors[0].msg)

    def test_a_template_directory_that_is_not_one_is_a_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = str(Path(directory) / "missing")
            with override_settings(INSTANCE_TEMPLATE_DIRS=[directory, missing]):
                warnings = check_instance_template_dirs(None)
        self.assertEqual([warning.id for warning in warnings], ["base.W001"])
        self.assertIn(missing, warnings[0].msg)


class OperatorDocsTest(SimpleTestCase):
    """The instance theming page names every token the catalogue lists, so an
    operator reading it knows the whole set. Describes:
    docs/installation/guides/instance-theming.md."""

    def test_every_token_is_documented(self):
        text = THEMING_DOCS.read_text()
        self.assertEqual(
            [token.name for token in TOKENS if f"`{token.name}`" not in text], []
        )

    def test_the_docs_name_no_token_the_catalogue_lacks(self):
        named = set(re.findall(r"`(--(?:bs|oep)-[\w-]+)`", THEMING_DOCS.read_text()))
        self.assertEqual(named - {token.name for token in TOKENS}, set())
