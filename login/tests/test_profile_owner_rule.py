"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Every route under ``profile/<user_id>/`` answers its owner only.

The rule lives in ``login/access.py``. A logged-in caller with another id gets
404 (the same for an id that exists and one that does not, so the answer says
nothing about which accounts exist), an anonymous caller is sent to the login
page, or gets a bare 401 when the request came from htmx. There is no
exemption for platform admins.
"""  # noqa: 501

import re
from functools import wraps
from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.shortcuts import resolve_url
from django.test import RequestFactory, TestCase
from django.urls import URLResolver, get_resolver, re_path, reverse
from django.urls.resolvers import RegexPattern
from django.views.decorators.cache import never_cache
from django.views.generic import View
from rest_framework.authtoken.models import Token

from base.tests import get_urlpattern_params
from dataedit.models import Dataset, PeerReview, PeerReviewManager, Table
from login.access import (
    ProfileOwnerRequiredMixin,
    enforces_owner_rule,
    profile_owner_required,
)
from login.models import ADMIN_PERM, UserPermission, myuser
from login.tests.helpers import HTMX, act_as, make_user


def without_csrf(response) -> str:
    """The body with its per-render CSRF tokens blanked out."""
    return re.sub(
        r'(csrfmiddlewaretoken" value=|csrfToken = )"[^"]*"',
        r"\1",
        response.content.decode(),
    )


class OwnerRuleFixture(TestCase):
    """Owner A holds a draft and a published table; B holds nothing of A's."""

    owner_table_draft = "owner_rule_draft_marker"
    owner_table_published = "owner_rule_published_marker"

    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user("OwnerRuleA")
        cls.foreign = make_user("OwnerRuleB")
        cls.platform_admin = make_user("OwnerRuleAdmin", is_admin=True)
        for name, published in (
            (cls.owner_table_draft, False),
            (cls.owner_table_published, True),
        ):
            table = Table.objects.create(
                name=name,
                is_publish=published,
                oemetadata={"resources": [{"name": name}]},
            )
            UserPermission.objects.create(
                holder=cls.owner, table=table, level=ADMIN_PERM
            )

    def assert_no_owner_tables(self, response):
        body = response.content.decode()
        self.assertNotIn(self.owner_table_draft, body)
        self.assertNotIn(self.owner_table_published, body)


class TablesListIsTheOwnersOnlyTests(OwnerRuleFixture):
    """The tables list, page and htmx partial, shows nothing to anyone else."""

    queries = (
        {},
        {"search": ""},
        {"search": "owner_rule"},
        {"draft_page": "1"},
        {"published_page": "1"},
    )

    def url(self):
        return reverse("login:tables", kwargs={"user_id": self.owner.pk})

    def test_owner_sees_own_tables_in_the_partial(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url(), **HTMX)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner_table_draft)

    def test_foreign_caller_gets_404_and_no_table_names(self):
        self.client.force_login(self.foreign)
        for query in self.queries:
            for headers in ({}, HTMX):
                with self.subTest(query=query, htmx=bool(headers)):
                    response = self.client.get(self.url(), query, **headers)
                    self.assertEqual(response.status_code, 404)
                    self.assert_no_owner_tables(response)

    def test_anonymous_caller_gets_no_table_names(self):
        for query in self.queries:
            for headers, status in (({}, 302), (HTMX, 401)):
                with self.subTest(query=query, htmx=bool(headers)):
                    response = self.client.get(self.url(), query, **headers)
                    self.assertEqual(response.status_code, status)
                    self.assert_no_owner_tables(response)

    def test_platform_admin_is_not_exempt(self):
        self.client.force_login(self.platform_admin)
        response = self.client.get(self.url(), **HTMX)
        self.assertEqual(response.status_code, 404)
        self.assert_no_owner_tables(response)


def routes_capturing(param, resolver, inherited=frozenset()):
    """Every URL pattern below ``resolver`` whose address captures ``param``.

    A parameter captured by an ``include()`` prefix counts for every route
    below it, so a ``user_id`` in a prefix covers all of its children.
    """
    for entry in resolver.url_patterns:
        captured = inherited | set(get_urlpattern_params(entry))
        if isinstance(entry, URLResolver):
            yield from routes_capturing(param, entry, captured)
        elif param in captured:
            yield entry


class EveryProfileRouteCarriesTheRuleTest(TestCase):
    """Structural: a new ``profile/<user_id>/`` route without the rule fails here.

    The same pattern as the OEKG API's ``AllowlistTest``: joining the profile
    has to be a decision somebody made, not something a route does by
    accident of where it was mounted. The walk starts at the site's root, so
    a ``user_id`` route in any app counts, however it is included.
    """

    def test_every_user_id_route_carries_the_owner_rule(self):
        routes = list(routes_capturing("user_id", get_resolver()))
        # a guard against the walk silently finding nothing
        self.assertIn("tables", {p.name for p in routes})
        missing = [p.name for p in routes if not enforces_owner_rule(p.callback)]
        self.assertEqual(missing, [], "profile routes without the owner rule")


def _plain_view(request, *args, **kwargs):
    return HttpResponse("served")


class _MixinAfterView(View, ProfileOwnerRequiredMixin):
    """Wrong order: View.dispatch runs and the mixin's never does."""

    def get(self, request, user_id):
        return HttpResponse("served")


class _DispatchOverridden(ProfileOwnerRequiredMixin, View):
    """Right order, but a dispatch of its own that skips the rule."""

    def dispatch(self, request, *args, **kwargs):
        return View.dispatch(self, request, *args, **kwargs)

    def get(self, request, user_id):
        return HttpResponse("served")


class _Guarded(ProfileOwnerRequiredMixin, View):
    def get(self, request, user_id):
        return HttpResponse("served")


@profile_owner_required
def _guarded_function(request, profile_user):
    return HttpResponse("served")


@wraps(_guarded_function)
def _impostor(request, user_id):
    """Looks like the guarded view (wraps copies its attributes) but is not."""
    return HttpResponse("served")


class OwnerRuleCheckSelfTests(TestCase):
    """The structural check must fail for a view on which the rule does not
    run, even when the view mentions the rule."""

    def test_wrong_class_is_rejected_and_really_skips_the_rule(self):
        self.assertFalse(enforces_owner_rule(_MixinAfterView.as_view()))
        # the reason it must be rejected: the rule does not run
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        response = _MixinAfterView.as_view()(request, user_id="1")
        self.assertEqual(response.status_code, 200)

    def test_dispatch_override_is_rejected(self):
        self.assertFalse(enforces_owner_rule(_DispatchOverridden.as_view()))

    def test_impostor_function_is_rejected(self):
        self.assertFalse(enforces_owner_rule(_impostor))
        self.assertFalse(enforces_owner_rule(_plain_view))

    def test_rule_wrapped_by_another_decorator_is_rejected(self):
        # the rule must be the outermost layer, so nothing runs before it
        self.assertFalse(enforces_owner_rule(never_cache(_guarded_function)))

    def test_wrapped_class_view_is_rejected(self):
        # functools.wraps copies view_class onto the wrapper, so a decorator
        # around as_view() looks like the class view while the wrapper runs
        # first; the rule must be the outermost layer for class views too
        for decorator in (login_required, never_cache):
            with self.subTest(decorator=decorator.__name__):
                wrapped = decorator(_Guarded.as_view())
                self.assertIs(wrapped.view_class, _Guarded)
                self.assertFalse(enforces_owner_rule(wrapped))

    def test_guarded_views_are_accepted(self):
        self.assertTrue(enforces_owner_rule(_Guarded.as_view()))
        self.assertTrue(enforces_owner_rule(_guarded_function))

    def test_walk_follows_include_prefixes(self):
        """A ``user_id`` captured by an include prefix covers its children."""
        prefix = URLResolver(
            RegexPattern(r"^profile/(?P<user_id>\d+)/"),
            [
                re_path(r"^unguarded$", _plain_view, name="unguarded"),
                re_path(r"^guarded$", _guarded_function, name="guarded"),
            ],
        )
        root = URLResolver(
            RegexPattern(r"^"),
            [
                re_path(r"^outside$", _plain_view, name="outside"),
                URLResolver(RegexPattern(r"^nested/"), [prefix]),
            ],
        )
        routes = {p.name: p for p in routes_capturing("user_id", root)}
        self.assertEqual(set(routes), {"unguarded", "guarded"})
        self.assertFalse(enforces_owner_rule(routes["unguarded"].callback))
        self.assertTrue(enforces_owner_rule(routes["guarded"].callback))


class ProfileRoutesTests(OwnerRuleFixture):
    """owner / foreign / anonymous x page / htmx, for every profile route."""

    dataset_name = "owner_rule_dataset"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Dataset.objects.create(
            name=cls.dataset_name,
            metadata={"name": cls.dataset_name, "title": "t", "description": ""},
            creator=cls.owner,
        )

    def routes(self):
        """(name, extra kwargs, status for the owner) for every GET route."""
        return [
            ("login:profile", {}, 200),
            ("login:datasets", {}, 200),
            ("login:dataset-action", {"action": "publish"}, 200),
            ("login:dataset-action", {"action": "create"}, 200),
            ("login:dataset-name-preview", {}, 200),
            ("login:tables", {}, 200),
            ("login:table-names", {}, 200),
            (
                "login:metadata-review-badge-icon",
                {"table_name": self.owner_table_draft},
                200,
            ),
            ("login:reviews", {}, 200),
            ("login:organizations", {}, 200),
            ("login:partial-organizations", {}, 200),
            ("login:settings", {}, 200),
            ("login:edit", {}, 200),
            # account deletion is not offered yet; the route answers 404,
            # to its owner too, instead of the 500 it used to raise
            ("login:account-delete", {}, 404),
        ]

    def post_routes(self):
        """(name, extra kwargs) for every route that takes a POST."""
        return [
            ("login:table-action-check", {"action": "publish"}),
            ("login:dataset-action", {"action": "delete"}),
            ("login:dataset-action", {"action": "create"}),
            ("login:dataset-action", {"action": "edit"}),
            ("login:edit", {}),
        ]

    def url(self, name, user_id, extra):
        return reverse(name, kwargs={"user_id": user_id, **extra})

    def test_owner_is_served(self):
        self.client.force_login(self.owner)
        for name, extra, status in self.routes():
            for headers in ({}, HTMX):
                with self.subTest(route=name, htmx=bool(headers)):
                    response = self.client.get(
                        self.url(name, self.owner.pk, extra), **headers
                    )
                    self.assertEqual(response.status_code, status)

    def test_foreign_caller_gets_404(self):
        self.client.force_login(self.foreign)
        for name, extra, _ in self.routes():
            for headers in ({}, HTMX):
                with self.subTest(route=name, htmx=bool(headers)):
                    response = self.client.get(
                        self.url(name, self.owner.pk, extra), **headers
                    )
                    self.assertEqual(response.status_code, 404)

    def test_anonymous_page_is_sent_to_login_with_next(self):
        login_url = resolve_url(settings.LOGIN_URL)
        for name, extra, _ in self.routes():
            with self.subTest(route=name):
                url = self.url(name, self.owner.pk, extra)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                location = urlsplit(response["Location"])
                self.assertEqual(location.path, login_url)
                self.assertEqual(parse_qs(location.query)["next"], [url])

    def test_anonymous_htmx_gets_401_without_body(self):
        for name, extra, _ in self.routes():
            with self.subTest(route=name):
                response = self.client.get(self.url(name, self.owner.pk, extra), **HTMX)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.content, b"")

    def test_unknown_id_answers_like_a_foreign_one(self):
        """No answer tells an existing account from a missing one."""
        self.client.force_login(self.foreign)
        missing_id = myuser.objects.order_by("-pk").first().pk + 1000
        for name, extra, _ in self.routes():
            with self.subTest(route=name):
                existing = self.client.get(self.url(name, self.owner.pk, extra))
                missing = self.client.get(self.url(name, missing_id, extra))
                self.assertEqual(existing.status_code, 404)
                self.assertEqual(missing.status_code, 404)
                self.assertEqual(without_csrf(existing), without_csrf(missing))

    def test_foreign_post_is_refused_before_anything_else(self):
        self.client.force_login(self.foreign)
        for name, extra in self.post_routes():
            with self.subTest(route=name):
                response = self.client.post(
                    self.url(name, self.owner.pk, extra),
                    {"title": "Hijacked", "table": self.owner_table_published},
                    **HTMX,
                )
                self.assertEqual(response.status_code, 404)

    def test_anonymous_post_is_refused(self):
        for name, extra in self.post_routes():
            with self.subTest(route=name):
                url = self.url(name, self.owner.pk, extra)
                self.assertEqual(self.client.post(url, {}).status_code, 302)
                self.assertEqual(self.client.post(url, {}, **HTMX).status_code, 401)


class RefusedGetsWriteNothingTests(OwnerRuleFixture):
    """Two profile GETs write; a refused caller must not reach either write."""

    def callers(self):
        return (("foreign", self.foreign), ("anonymous", None))

    def test_refused_settings_get_creates_no_token(self):
        Token.objects.filter(user=self.owner).delete()
        url = reverse("login:settings", kwargs={"user_id": self.owner.pk})
        for caller, user in self.callers():
            for headers in ({}, HTMX):
                with self.subTest(caller=caller, htmx=bool(headers)):
                    act_as(self.client, user)
                    self.client.get(url, **headers)
                    self.assertFalse(Token.objects.filter(user=self.owner).exists())

    def test_refused_reviews_get_leaves_the_review_manager_alone(self):
        review = PeerReview.objects.create(
            table=self.owner_table_published,
            reviewer=self.owner,
            contributor=self.foreign,
            review={},
        )
        manager = PeerReviewManager.objects.create(opr=review, is_open_since="stale")
        url = reverse("login:reviews", kwargs={"user_id": self.owner.pk})
        for caller, user in self.callers():
            for headers in ({}, HTMX):
                with self.subTest(caller=caller, htmx=bool(headers)):
                    act_as(self.client, user)
                    self.client.get(url, **headers)
                    manager.refresh_from_db()
                    self.assertEqual(manager.is_open_since, "stale")

        # the same GET by the owner does write, so the check above can fail
        self.client.force_login(self.owner)
        self.client.get(url)
        manager.refresh_from_db()
        self.assertNotEqual(manager.is_open_since, "stale")
