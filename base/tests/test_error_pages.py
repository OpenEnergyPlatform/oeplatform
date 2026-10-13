"""The error pages (#2652, spec #2632): a 404 and a 500 are an empty state at
page size, with no header band.

Each used to be a `<center>` of line breaks with the platypus at half the
width below it. Now each is `components/empty_state.html`: the platypus above
the title, the title as the page's one `h1`, the text below it. Asserted here,
as a browser receives them, with `DEBUG` off (as in production, where these
pages are the ones anybody sees):

- the status, and the one empty state with its image above its heading;
- no page header band, and nothing laid out by `<center>`, `<br>` or an
  inline style;
- the text is the text from before this ticket, apart from the one accepted
  change: "OEPlatypus:" became "OEPlatypus.", because the platypus it pointed
  down at now stands above it;
- the 500 keeps the button rule the restyled pages keep (the 404 is on the
  page lint's own list).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import TestCase, override_settings
from django.urls import path, reverse

from base.tests.html_tree import parse
from base.tests.page_lint import lint
from base.tests.test_page_header import SNAPSHOTS
from oeplatform.urls import urlpatterns as platform_urlpatterns


def boom(request):
    raise RuntimeError("an unexpected error")


# This module is the URLconf of the 500 test: the platform's routes (the shell
# reverses them) plus one view that fails.
urlpatterns = platform_urlpatterns + [path("boom/", boom)]
handler500 = "base.views.handler500"


@override_settings(DEBUG=False)
class ErrorPageTest(TestCase):
    def missing_page(self):
        return self.client.get("/no/such/page/")

    def unknown_project(self):
        return self.client.get(
            reverse("base:project_detail", kwargs={"project_id": "no-such-project"})
        )

    @override_settings(ROOT_URLCONF=__name__)
    def server_error(self):
        self.client.raise_request_exception = False
        return self.client.get("/boom/")

    def pages(self):
        """(label, response, status, snapshot) for each way to reach an error
        page. A snapshot is the page's text from before #2652 with the one
        accepted change made: "OEPlatypus:" became "OEPlatypus."."""
        return (
            ("missing page", self.missing_page(), 404, "error_404"),
            ("unknown project", self.unknown_project(), 404, "error_404"),
            ("server error", self.server_error(), 500, "error_500"),
        )

    def test_the_status(self):
        for label, response, status, _ in self.pages():
            with self.subTest(page=label):
                self.assertEqual(response.status_code, status)

    def test_one_empty_state_with_the_platypus_above_the_one_h1(self):
        for label, response, _, _ in self.pages():
            with self.subTest(page=label):
                main = parse(response.content.decode()).find("main")
                [state] = main.find_all(css_class="empty-state")
                image = state.find("img")
                [h1] = main.find_all("h1")
                self.assertEqual(image.attrs["alt"], "OEPlatypus")
                self.assertIn(h1, state.elements)
                self.assertLess(state.elements.index(image), state.elements.index(h1))

    def test_no_band_and_no_layout_by_markup(self):
        for label, response, _, _ in self.pages():
            with self.subTest(page=label):
                root = parse(response.content.decode())
                self.assertEqual(root.find_all("header", "page-header"), [])
                main = root.find("main")
                for tag in ("center", "br"):
                    self.assertEqual(main.find_all(tag), [])
                styled = [n for n in main.find_all() if "style" in n.attrs]
                self.assertEqual(styled, [])

    def test_texts_are_unchanged_but_for_the_platypus(self):
        for label, response, _, snapshot in self.pages():
            with self.subTest(page=label):
                main = parse(response.content.decode()).find("main")
                expected = (SNAPSHOTS / f"{snapshot}.txt").read_text().strip()
                self.assertEqual(main.text(), expected)

    def test_the_server_error_keeps_the_button_rule(self):
        self.assertEqual(lint(self.server_error().content.decode()), [])
