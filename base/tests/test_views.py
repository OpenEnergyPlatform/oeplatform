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
        errors = []

        # find all templates
        for path in root_dir.glob("*/templates/**/*.html"):
            with open(path, encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    # find href and src tags
                    for match in re.findall(
                        r"(src|href)[ ]*=[ ]*('([^']*)'|\"([^\"]*)\")", line
                    ):
                        # get string between quotes
                        value = match[2] or match[3]
                        logging.info(value)

                # if app not in resolvers:
                #    resolvers[app] = get_app_reverse_lookup_names_and_kwargs(app)

                # if match not in resolvers[app]:
                #    errors.add((path, match))
        if errors:
            error_txt = "Errors in urls in templates:\n\n" + "\n".join(errors)
            raise Exception(error_txt)
