"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Static files are named after their content (#2604), so a browser that cached
last release's stylesheet asks for this release's under a new address instead
of reusing the old one. ``ManifestStaticFilesStorage`` does that, and brings
two things a deploy must get right: ``collectstatic`` refuses a stylesheet
whose ``url()`` points at nothing, and ``compress`` must run after it, under
the same ``DEBUG`` as the server.
"""  # noqa: 501

import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from django.conf import settings
from django.templatetags.static import static
from django.test import SimpleTestCase

# A name ManifestStaticFilesStorage hashed: twelve hex digits before the
# extension.
HASHED = r"\.[0-9a-f]{12}\.\w+"

DEPLOY_SETTINGS = """
import oeplatform.securitysettings as _local

# An instance's two theming settings (#2637), as its securitysettings.py carries
# them, so oeplatform.settings reads them on import below.
_local.INSTANCE_STYLESHEETS = [{stylesheet!r}]
_local.INSTANCE_TEMPLATE_DIRS = [{templates!r}]

import oeplatform.settings as _configured

globals().update(
    {{key: value for key, value in vars(_configured).items() if key.isupper()}}
)
DEBUG = False
STATIC_ROOT = COMPRESS_ROOT = {static_root!r}
# STATICFILES_DIRS is host configuration and holds Vite's build output, which
# Vite has hashed already and which CI never builds. What is checked here is
# what this repository ships in the apps' static directories, and an instance's
# stylesheet beside it.
STATICFILES_DIRS = [{instance_static!r}]
"""

SHELLS = ["base", "base-full", "base-profile", "base-sidebar", "base-wide-react"]

RENDER_THE_SHELLS = """
import json

import django

django.setup()

from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory

request = RequestFactory().get("/")
request.user = AnonymousUser()
print(json.dumps({{
    shell: render_to_string(f"base/{{shell}}.html", request=request)
    for shell in {shells!r}
}}))
"""

INSTANCE_STYLESHEET = "instance/theme.css"
INSTANCE_NAME = "Example Grid Platform"


class DeploySequenceTest(SimpleTestCase):
    """``collectstatic``, then ``compress``, then a page, as a deploy runs
    them: each in its own process, with the configured storage and ``DEBUG``
    off, for an instance that sets both theming settings, as the derived image
    in docs/installation/guides/instance-theming.md does.

    Processes rather than ``call_command``, because the suite's own storage
    deliberately differs (see ``TestRunStorageTest``), and because
    django-compressor keeps its storage and offline manifest in module
    globals that a forced ``compress`` in this process would write through
    into the real ``static/``.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        root = Path(cls.directory.name)
        instance_static = root / "instance_static"
        (instance_static / "instance").mkdir(parents=True)
        (instance_static / INSTANCE_STYLESHEET).write_text(
            ":root { --bs-primary: #7a1f5d; }\n"
        )
        templates = root / "instance_templates"
        (templates / "brand").mkdir(parents=True)
        (templates / "brand" / "name.html").write_text(f"{INSTANCE_NAME}\n")
        (root / "deploy_settings.py").write_text(
            DEPLOY_SETTINGS.format(
                stylesheet=INSTANCE_STYLESHEET,
                templates=str(templates),
                static_root=str(root / "static"),
                instance_static=str(instance_static),
            )
        )

        cls.collected = cls._run("manage.py", "collectstatic", "--noinput")
        cls.compressed = cls._run("manage.py", "compress", "--force")
        cls.rendered = cls._run(
            "-c", textwrap.dedent(RENDER_THE_SHELLS.format(shells=SHELLS))
        )
        cls.shells = (
            json.loads(cls.rendered.stdout) if cls.rendered.returncode == 0 else {}
        )

    @classmethod
    def _run(cls, *arguments):
        return subprocess.run(
            [sys.executable, *arguments],
            capture_output=True,
            text=True,
            cwd=settings.BASE_DIR,
            env={
                **os.environ,
                "DJANGO_SETTINGS_MODULE": "deploy_settings",
                "PYTHONPATH": os.pathsep.join(
                    [cls.directory.name, str(settings.BASE_DIR)]
                ),
            },
        )

    def assertSucceeded(self, result):
        self.assertEqual(result.returncode, 0, result.stderr[-3000:])

    def test_collectstatic_finds_every_file_a_stylesheet_points_at(self):
        # Post-processing rewrites each CSS url() to the hashed name of its
        # target, and stops the whole collection when the target is missing.
        self.assertSucceeded(self.collected)

    def test_compress_runs_on_the_collected_files(self):
        self.assertSucceeded(self.compressed)

    def test_a_page_links_its_static_files_by_content(self):
        self.assertSucceeded(self.rendered)
        self.assertRegex(self.shells["base"], rf'href="/static/favicon{HASHED}"')

    def test_every_shell_finds_the_bundle_compress_wrote(self):
        # The offline manifest is keyed on the block's rendered content, which
        # includes every {% static %} inside it. A page that renders at all
        # has found its keys, which is why compress must run under the
        # server's DEBUG: under DEBUG, {% static %} returns plain names. The
        # five shells share one head (base/_head.html), so one bundle.
        self.assertSucceeded(self.rendered)
        bundles = {
            shell: re.findall(rf'href="(/static/CACHE/css/output{HASHED})"', html)
            for shell, html in self.shells.items()
        }
        self.assertEqual(sorted(bundles), sorted(SHELLS))
        self.assertEqual(len({tuple(found) for found in bundles.values()}), 1)
        self.assertEqual(len(bundles["base"]), 1)

    def test_every_shell_links_the_instance_stylesheet_by_content_last(self):
        self.assertSucceeded(self.rendered)
        for shell, html in self.shells.items():
            with self.subTest(shell=shell):
                links = re.findall(
                    r'<link rel="stylesheet" href="([^"]*)"',
                    html[: html.index("</head>")],
                )
                self.assertRegex(links[-1], rf"^/static/instance/theme{HASHED}$")

    def test_a_template_in_the_instance_directory_wins(self):
        self.assertSucceeded(self.rendered)
        self.assertIn(f'alt="{INSTANCE_NAME} home"', self.shells["base"])


class TestRunStorageTest(SimpleTestCase):
    """The suite renders pages without having run ``collectstatic``, so it
    serves plain names, as Django's documentation advises for
    ``ManifestStaticFilesStorage``, but refuses the names the configured
    storage refuses (``oeplatform.runner.FindableStaticFilesStorage``).
    ``DeploySequenceTest`` checks the real storage."""

    def test_a_test_run_uses_plain_names(self):
        self.assertEqual(static("css/base-style.css"), "/static/css/base-style.css")

    def test_a_name_no_finder_has_is_refused(self):
        # As the configured storage refuses a name missing from its manifest,
        # so every page the suite renders checks its {% static %} names. In
        # production such a name fails the whole page, where before it was
        # one missing file. Each of these was in a template.
        for name in [
            "css/no-such-file.css",
            "/css/base-style.css",
            "logos/project/",
            "/media/logos/a-model-logo.png",
        ]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                static(name)


class FinderOrderTest(SimpleTestCase):
    def test_finders_are_asked_in_a_fixed_order(self):
        # A set iterates in a per-process order, so a file overridden through
        # STATICFILES_DIRS would win in some processes and lose in others.
        self.assertEqual(
            list(settings.STATICFILES_FINDERS),
            [
                "django.contrib.staticfiles.finders.FileSystemFinder",
                "django.contrib.staticfiles.finders.AppDirectoriesFinder",
                "compressor.finders.CompressorFinder",
            ],
        )
        self.assertIsInstance(settings.STATICFILES_FINDERS, (list, tuple))
