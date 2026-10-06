"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The term search address (#2292): which endpoint an instance uses, and that the
metadata editor and the unit picker use that one rather than a fixed address.
"""  # noqa: 501

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils.html import escapejs

from oeplatform.oeo_search import OWN_OEO_SEARCH, PUBLIC_OEO_SEARCH, oeo_search_url

ELSEWHERE = "https://search.example.org/api/oeo-search"
URLS = {"oeo_search": ELSEWHERE}
# the templates write it through escapejs, which escapes the hyphen
IN_SCRIPT = escapejs(ELSEWHERE)


class OeoSearchUrlTest(SimpleTestCase):
    def test_an_instance_with_its_own_lookup_searches_itself(self):
        self.assertEqual(oeo_search_url(True, {}), OWN_OEO_SEARCH)

    def test_an_instance_without_one_uses_the_public_endpoint(self):
        self.assertEqual(oeo_search_url(False, {}), PUBLIC_OEO_SEARCH)

    def test_the_environment_overrides_both(self):
        for use_loep in (True, False):
            with self.subTest(use_loep=use_loep):
                self.assertEqual(
                    oeo_search_url(use_loep, {"OEO_SEARCH_URL": ELSEWHERE}), ELSEWHERE
                )


@override_settings(EXTERNAL_URLS=URLS)
class SearchUsersTest(TestCase):
    def test_the_metadata_editor_searches_the_configured_endpoint(self):
        page = self.client.get(reverse("dataedit:oemetabuilder")).content.decode()
        self.assertIn(f'config.oeo_search_url = "{IN_SCRIPT}"', page)
        self.assertNotIn(escapejs(PUBLIC_OEO_SEARCH), page)

    def test_the_unit_picker_searches_the_configured_endpoint(self):
        html = render_to_string(
            "oeo_ext/partials/unit_element.html",
            request=RequestFactory().get("/"),
        )
        self.assertIn(f"{IN_SCRIPT}?query=", html)
        self.assertNotIn(escapejs(PUBLIC_OEO_SEARCH), html)
