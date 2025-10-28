"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
import re
from pathlib import Path

from base.tests import TestViewsTestCase, get_app_reverse_lookup_names_and_kwargs
from oeplatform.settings import BASE_DIR


class TestViewsBase(TestViewsTestCase):
    """Call all (most) views"""

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET
        """
        self.get("base:about")
        self.get("base:contact")
        self.get("base:discussion")
        self.get("base:faq")
        self.get("base:home")
        self.get("base:legal-privacy-policy")
        self.get("base:legal-tou")
        self.get("base:robots")
        self.get("base:tutorials")
        self.get("base:project_detail", kwargs={"project_id": "sirop"})

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
