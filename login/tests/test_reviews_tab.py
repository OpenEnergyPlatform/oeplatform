"""The profile's Reviews tab: its scripts, its Delete and its lists (#2658).

It used to load `opr_reviewer.js`, first as a classic script the browser
refused ("Cannot use import statement outside a module"), then as a module
(#2634) whose review-page handlers logged errors here and which never bound
the tab's Delete. Since #2658 the tab binds only its Delete, in its own small
script (#2674).

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.urls import reverse

from base.tests import TestViewsTestCase
from base.tests.test_page_lint import Page, PageFixture
from modelview.tests.html import element_markup, element_with_id, elements_with_class


class ReviewsTabScriptTest(TestViewsTestCase):
    def test_the_tab_loads_none_of_the_review_pages_scripts(self):
        html = self.get(
            "login:reviews", kwargs={"user_id": self.user.pk}, logged_in=True
        ).content.decode()

        self.assertNotRegex(html, r"<script\b[^>]*peer_review/")


class ReviewsTabTest(PageFixture):
    def tab(self):
        return self.html(Page("login:reviews", {"user_id": "{user}"}, True))

    def test_delete_asks_the_house_dialog_for_the_active_review(self):
        # #2674: the button had no handler on this page.
        delete = element_with_id(self.tab(), "peer_review-delete")

        self.assertIn(f'data-review-id="{self.peer_review.pk}"', delete)
        self.assertIn('data-confirm-title="Delete review?"', delete)
        self.assertIn('data-confirm-verb="Delete review"', delete)
        self.assertIn("data-confirm-danger", delete)

    def test_the_tab_sets_the_csrf_cookie_its_delete_needs(self):
        # Nothing else on the tab asks for a token, and without the cookie
        # the delete is refused 403 (found in the browser).
        response = self.get(
            "login:reviews", kwargs={"user_id": self.user.pk}, logged_in=True
        )

        self.assertIn("csrftoken", response.cookies)
        self.assertIn(
            reverse("login:delete_peer_review_simple"), response.content.decode()
        )

    def test_all_reviews_lists_the_users_review(self):
        # The list read context keys renamed away by the organizations work,
        # so it showed nothing.
        html = element_markup(self.tab(), "main-content")

        listed = elements_with_class(html, "profile-rvw__item--done")
        self.assertEqual(len(listed), 1)
        self.assertIn(self.table_name, listed[0])

    def test_statuses_are_badges(self):
        html = element_markup(self.tab(), "main-content")

        cards = elements_with_class(html, "profile-rvw__item")
        self.assertEqual(len(cards), 3)  # the active one, the waiting one, the list
        for card in (cards[0], cards[2]):
            self.assertRegex(card, r'class="badge badge--\w+')
        self.assertNotIn("profile-rvw__item-status", html)
