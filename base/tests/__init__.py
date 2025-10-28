"""
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
import re
from typing import Iterable

from django.urls import URLPattern, URLResolver, get_resolver
from django.urls.resolvers import RegexPattern, RoutePattern


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
