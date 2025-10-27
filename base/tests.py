"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
import re
from pathlib import Path
from typing import Iterable

from django.test import TestCase
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.urls.resolvers import RegexPattern, RoutePattern

from oeplatform.settings import BASE_DIR


def recursively_get_patterns(resolver: URLResolver) -> Iterable[URLPattern]:
    for p in resolver.url_patterns:
        if isinstance(p, URLPattern):
            yield p
        elif isinstance(p, URLResolver):
            yield from recursively_get_patterns(p)
        else:
            raise NotImplementedError(type(p))


def get_urlpattern_params(pattern: URLPattern) -> list[str]:
    """get list of parameter names passed to url reverse lookup"""
    pattern2 = pattern.pattern
    if isinstance(pattern2, RegexPattern):
        regex = re.compile(
            # TODO: better way than using protected attribute?
            pattern2._regex  # type:ignore
        )
        return list(regex.groupindex.keys())
    elif isinstance(pattern2, RoutePattern):
        # TODO: does this really work?
        return list(pattern2.converters.keys())
    else:
        raise NotImplementedError(type(pattern))


def get_app_reverse_lookup_names_and_kwargs(
    app_name: str | None = None,
) -> dict[str, list[str]]:
    resolver_url = f"{app_name}.urls" if app_name else None
    resolver = get_resolver(resolver_url)
    results = {}
    for pattern in recursively_get_patterns(resolver):
        name = pattern.name
        if not name:
            logging.warning("no reverse lookup name for %s: %s", app_name, pattern)
            continue
        name = f"{app_name}:{name}" if app_name else name
        if name in results:
            logging.warning("non unique reverse lookup name: %s", name)
            continue
        results[name] = get_urlpattern_params(pattern)
    return results


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

            if name in {"sparql_endpoint"}:
                # skip because POST
                continue

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
