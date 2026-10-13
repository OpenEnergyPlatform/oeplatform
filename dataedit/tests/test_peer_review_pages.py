"""The peer review pages and the profile's Reviews tab on house components (#2658).

The two review templates carried their own copies of one stylesheet, and their
actions took their look from the containers around them. Every action now
carries its role on itself (the page lint holds that, `base/tests/
test_page_lint.py`); these tests pin what the lint cannot see.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from pathlib import Path

from django.conf import settings
from django.urls import reverse

from base.tests.test_page_lint import Page, PageFixture, classes_of
from modelview.tests.html import element_markup, elements_with_class

TEMPLATES = Path(settings.BASE_DIR) / "dataedit" / "templates" / "dataedit"


def opening_tag(html: str, element_id: str) -> str:
    found = re.search(r'<[a-z]+\b[^>]*\bid="%s"[^>]*>' % element_id, html)
    assert found, element_id
    return found.group(0)


class PeerReviewPagesTest(PageFixture):
    def pages(self):
        review = {"table": "{table}", "review_id": "{review}"}
        return {
            "reviewer": self.html(Page("dataedit:peer_review_reviewer", review, True)),
            "contributor": self.html(
                Page("dataedit:peer_review_contributor", review, True)
            ),
        }

    def test_neither_template_carries_a_stylesheet_of_its_own(self):
        for name in ("opr_review.html", "opr_contributor.html"):
            with self.subTest(template=name):
                self.assertNotIn("<style", (TEMPLATES / name).read_text("utf-8"))

    def test_the_field_saves_are_the_panels_primary_action(self):
        # They were yellow and red, recoloured by the chosen state.
        for role, html in self.pages().items():
            for save in ("submitButton", "submitCommentButton"):
                with self.subTest(page=role, button=save):
                    self.assertLessEqual(
                        {"btn", "btn-primary"}, classes_of(opening_tag(html, save))
                    )

    def test_the_bars_actions_carry_their_roles(self):
        roles = {
            "submit_summary": "btn-primary",
            "peer_review-save": "btn-secondary",
            "peer_review-cancel": "btn-secondary",
        }
        for page, html in self.pages().items():
            for button, role in roles.items():
                with self.subTest(page=page, button=button):
                    self.assertIn(role, classes_of(opening_tag(html, button)))
        reviewer = self.pages()["reviewer"]
        self.assertIn(
            "btn-outline-danger",
            classes_of(opening_tag(reviewer, "peer_review-delete")),
        )

    def test_the_field_navigation_buttons_have_names(self):
        for page, html in self.pages().items():
            with self.subTest(page=page):
                nav = elements_with_class(html, "review__btn-nav")[0]
                self.assertIn('aria-label="Previous field"', nav)
                self.assertIn('aria-label="Next field"', nav)


class ReviewsTabTest(PageFixture):
    def tab(self):
        return self.html(Page("login:reviews", {"user_id": "{user}"}, True))

    def test_delete_asks_the_house_dialog_for_the_active_review(self):
        # #2674: the button had no handler on this page.
        delete = opening_tag(self.tab(), "peer_review-delete")

        self.assertIn(f'data-review-id="{self.peer_review.pk}"', delete)
        self.assertIn('data-confirm-title="Delete review?"', delete)
        self.assertIn('data-confirm-verb="Delete review"', delete)
        self.assertIn("data-confirm-danger", delete)

    def test_the_delete_posts_with_the_pages_own_token(self):
        # Which scripts the tab loads: login/tests/test_reviews_tab.py.
        html = self.tab()

        self.assertIn(reverse("login:delete_peer_review_simple"), html)
        # Nothing else on the tab sets the CSRF cookie the request needs.
        self.assertIn('"X-CSRFToken"', html)

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
