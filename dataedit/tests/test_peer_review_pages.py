"""The peer review pages on house components (#2658).

The two review templates carried their own copies of one stylesheet, and their
actions took their look from the containers around them. Every action now
carries its role on itself (the page lint holds that, `base/tests/
test_page_lint.py`); these tests pin what the lint cannot see. The profile's
Reviews tab: login/tests/test_reviews_tab.py.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from pathlib import Path

from django.conf import settings

from base.tests.test_page_lint import Page, PageFixture, classes_of
from modelview.tests.html import element_with_id, elements_with_class

TEMPLATES = Path(settings.BASE_DIR) / "dataedit" / "templates" / "dataedit"


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

    def test_the_field_saves_are_secondary(self):
        # They were yellow and red, recoloured by the chosen state. Submit is
        # the page's one primary action (Finish replaces it once it is
        # disabled).
        for role, html in self.pages().items():
            for save in ("submitButton", "submitCommentButton"):
                with self.subTest(page=role, button=save):
                    self.assertLessEqual(
                        {"btn", "btn-secondary"},
                        classes_of(element_with_id(html, save)),
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
                    self.assertIn(role, classes_of(element_with_id(html, button)))
        reviewer = self.pages()["reviewer"]
        self.assertIn(
            "btn-outline-danger",
            classes_of(element_with_id(reviewer, "peer_review-delete")),
        )

    def test_the_field_navigation_buttons_have_names(self):
        for page, html in self.pages().items():
            with self.subTest(page=page):
                nav = elements_with_class(html, "review__btn-nav")[0]
                self.assertIn('aria-label="Previous field"', nav)
                self.assertIn('aria-label="Next field"', nav)
