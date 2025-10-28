"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
import re
from pathlib import Path

from django.test import TestCase
from django.urls import reverse

from base.tests import get_app_reverse_lookup_names_and_kwargs
from oeplatform.settings import BASE_DIR


class TestViewsBase(TestCase):
    """Call all (most) views"""

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET
        """

        default_kwargs = {"project_id": "sirop"}

        for name, kwarg_names in sorted(
            get_app_reverse_lookup_names_and_kwargs("base").items()
        ):

            kwargs = {k: default_kwargs[k] for k in kwarg_names}
            url = reverse(name, kwargs=kwargs)

            resp = self.client.get(path=url)
            self.assertTrue(resp.status_code < 400)

    def test_urls_in_templates(self):
        resolvers = {}
        root_dir = Path(BASE_DIR)
        errors = set()
        # find all templates
        for path in root_dir.glob("**/templates/**/*.html"):
            # skip venv/env/.env/.venv
            if "env" in path.as_posix():
                continue

            with open(path, encoding="utf-8") as f:
                text = f.read()

            # find all url lookup
            for match in re.findall(r"\{% url [\"']([^\"']*)", text):
                app = match.split(":")[0] if ":" in match else None

                if app not in resolvers:
                    resolvers[app] = get_app_reverse_lookup_names_and_kwargs(app)

                if match not in resolvers[app]:
                    errors.add((path, match))
        if errors:
            logging.error(sorted(errors))
            raise Exception("could not find some reverse urls in templates")
