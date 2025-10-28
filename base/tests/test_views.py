"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from pathlib import Path

from base.tests import TestViewsTestCase, get_app_reverse_lookup_names_and_kwargs
from oeplatform.settings import BASE_DIR, EXTERNAL_URLS


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

        EXTERNAL_URLS_REV = {v: k for k, v in EXTERNAL_URLS.items()}

        def unquote(x):
            x = x.strip()
            if len(x) > 1 and x[0] == x[-1] and x[0] in {"'", '"'}:
                return x[1:-1]
            return x

        def can_resolve_name(name: str) -> bool:
            app = name.split(":")[0] if ":" in name else name
            if app not in resolvers:
                try:
                    resolvers[app] = get_app_reverse_lookup_names_and_kwargs(app)
                except Exception:
                    return False
            return name in resolvers[app]

        # find all templates
        for path in root_dir.glob("*/templates/**/*.html"):
            with open(path, encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    location = f"{path}:{idx+1}"
                    # find href and src tags
                    for match in re.findall(
                        r"(src|href)[ ]*=[ ]*('([^']+)'|\"([^\"]+)\")", line
                    ):
                        # get string between quotes
                        value = unquote(match[1])
                        if re.match(r"^({%|#|\?|{{|mailto:|javascript:)", value):
                            # find reverse url pattern
                            match_url = re.match(".*{% url[ ]+(.*)%}", value)
                            if match_url:
                                # get string between quotes
                                url_value = match_url.groups()[0].strip()
                                # get only first part (name)
                                reverse_name = unquote(url_value.split(" ")[0])
                                if not can_resolve_name(reverse_name):
                                    errors.append(
                                        (location, "Cannot reverse url", url_value)
                                    )
                        elif re.match("^(http:|https:|//)", value):
                            # should be external link
                            if value in EXTERNAL_URLS_REV:
                                errors.append(
                                    (
                                        location,
                                        f"Use existing EXTERNAL_URLS.{EXTERNAL_URLS_REV[value]}",  # noqa:501
                                        value,
                                    )
                                )
                            else:
                                errors.append(
                                    (location, "Use (create new) EXTERNAL_URLS", value)
                                )
                        elif re.match("^/static/", value):
                            # should be static link
                            errors.append((location, "Use {% static %}", value))
                        else:
                            # other (should probably be reverse lookup)
                            errors.append((location, "Use {% url %}", value))

        if errors:
            errors = [" ".join(e) for e in errors]
            error_txt = "Errors in urls in templates:\n\n" + "\n".join(errors)
            raise Exception(error_txt)
