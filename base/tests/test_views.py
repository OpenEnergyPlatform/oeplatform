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

        EXTERNAL_URLS_REV = {v: k for k, v in EXTERNAL_URLS.items()}

        def unquote(x):
            x = x.strip()
            if len(x) > 1 and x[0] == x[-1] and x[0] in {"'", '"'}:
                return x[1:-1]
            return x

        def can_resolve_name(name: str) -> bool:
            if ":" in name:
                app = name.split(":")[0]
            elif name.startswith("account_"):
                app = "allauth"  # allauth does not use prefix, apparently
                name = f"{app}:{name}"
            else:
                app = None

            if app not in resolvers:
                try:
                    resolvers[app] = get_app_reverse_lookup_names_and_kwargs(app)
                except Exception:
                    return False
            return name in resolvers[app]

        def find_url_problem(url: str, location: str) -> str | None:
            # get string between quotes
            value = unquote(url)
            if not value:
                return None
            elif match := re.match(r".*EXTERNAL_URLS\.([^ }]+)", value):
                key = match.groups()[0]
                if key not in EXTERNAL_URLS:
                    return f"not defined in EXTERNAL_URLS: {key} in {location}"
                else:
                    return None
            elif re.match(r"^({%|#|\?|{{|mailto:|javascript:)", value):
                # find reverse url pattern
                match_url = re.match(".*{% url[ ]+(.*)%}", value)
                if match_url:
                    # get string between quotes
                    url_value = match_url.groups()[0].strip()
                    # get only first part (name)
                    reverse_name = unquote(url_value.split(" ")[0])
                    if not can_resolve_name(reverse_name):
                        return f"Cannot reverse url: {url_value} in {location}"
            elif re.match("^(http:|https:|//)", value):
                # should be external link
                if value in EXTERNAL_URLS_REV:
                    return f"Use existing EXTERNAL_URLS.{EXTERNAL_URLS_REV[value]}: {value} in {location}"  # noqa: 501
                else:
                    return f"Use (create new) EXTERNAL_URLS: {value} in {location}"
            elif re.match("^/static/", value):
                # should be static link
                return f"Use %static: {value} in {location}"
            else:
                # other (should probably be reverse lookup)
                return f"Use %url: {value} in {location}"

        errors = []

        # find all templates
        for path in root_dir.glob("*/templates/**/*.html"):
            with open(path, encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    # find href and src tags
                    for match in re.findall(
                        r"(src|href|action|hx-post)[ ]*=[ ]*('([^']+)'|\"([^\"]+)\")",
                        line,
                    ):
                        error = find_url_problem(
                            url=match[1], location=f"{path}:{idx + 1}"
                        )
                        if error:
                            errors.append(error)
        if errors:
            error_txt = "Errors in urls in templates:\n\n" + "\n".join(errors)
            raise Exception(error_txt)
