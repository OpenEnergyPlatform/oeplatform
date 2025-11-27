"""
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
import re
from typing import Iterable
from urllib.parse import urlencode

from django.http import HttpResponse
from django.test import TestCase
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.urls.resolvers import RegexPattern, RoutePattern

from login.models import GroupMembership, UserGroup
from login.models import myuser as User
from oeplatform.settings import IS_TEST

logger = logging.getLogger("oeplatform")


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
            logger.warning("no reverse lookup name for %s: %s", app_name, pattern)
            continue
        name = f"{app_name}:{name}" if app_name else name
        if name in results:
            logger.warning("non unique reverse lookup name: %s", name)
            continue
        results[name] = get_urlpattern_params(pattern)
    return results


class TestViewsTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        # ensure IS_TEST is set correctly
        if not IS_TEST:
            raise Exception("IS_TEST is not True")
        super(TestViewsTestCase, cls).setUpClass()

        # create test user
        cls.user = User.objects.create_user(  # type: ignore
            name="test", email="test@test.test", affiliation="test"
        )
        cls.group = UserGroup.objects.create()
        GroupMembership.objects.create(user=cls.user, group=cls.group)

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        cls.group.delete()
        super(TestViewsTestCase, cls).tearDownClass()

    def get(
        self,
        view_name: str,
        args: list | None = None,
        kwargs: dict | None = None,
        query: dict | None = None,
        logged_in: bool = False,
    ) -> HttpResponse:

        # construct url
        url = reverse(view_name, args=args, kwargs=kwargs)
        if query:
            url += f"?{urlencode(query)}"

        if logged_in:
            self.client.force_login(self.user)
        else:
            self.client.logout()

        resp = self.client.get(url)
        self.assertTrue(resp.status_code < 400, msg=f"{view_name}: {resp}")
        return resp
