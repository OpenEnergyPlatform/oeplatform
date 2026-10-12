"""The page header (#2639, spec #2632): a band under the navbar on the pages
that started with their title glued under it.

The band is the house component ``page_header`` in the platform's area/trail
form: the area (with its icon) on a line of its own, then a breadcrumb trail
whose last part is the page's ``h1``. Asserted here, as a browser receives the
pages:

- the include alone: one ``h1``, as the trail's last, current item; the trail is
  a ``<nav>`` around an ordered list holding nothing but its items (a separator
  is drawn by the item before it, so it can never start a wrapped line); the
  optional slots render only when given;
- each page this ticket gives a band: exactly one ``h1``, inside the band, as
  the trail's last part, with the area and trail its row in ``PAGES`` names;
- each page's text is the text it had before this ticket, word for word, apart
  from the labels the band borrows from the navbar and footer (and terms of
  use's accepted title, the one new heading);
- account pages and error pages render no band.

Structure only, never CSS. That the band and the content share their edges
is measured in a browser and shown in the pull request.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from pathlib import Path
from typing import NamedTuple

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import reverse
from django.views.defaults import server_error

from base.tests import TestViewsTestCase
from base.tests.html_tree import parse

BAND = "page-header"
AREA = "page-header__area"
TRAIL = "page-header__trail"
COMPONENT = "components/page_header.html"

# What each page's text read as before this ticket (main element, whitespace
# collapsed), captured from the unchanged templates. A later ticket that moves
# these pages' layout keeps them as they are; one that changes a text on
# purpose (spec #2632's accepted list) updates its snapshot in the same change.
SNAPSHOTS = Path(__file__).parent / "page_texts"

ABOUT = "base:about"
OVERVIEW = (("Overview", ABOUT),)


class Page(NamedTuple):
    view: str
    area: str
    # The trail's links as (label, view), in order; the title follows them.
    links: tuple
    title: str
    kwargs: dict | None = None
    # A page of the signed-in user's own: their id goes into its URL and links.
    own: bool = False


PAGES = {
    "about": Page(ABOUT, "About", (), "Open Energy Family and Open Energy Platform"),
    "steering_committee": Page(
        "base:oefamily-sc", "About", OVERVIEW, "Open Energy Family Steering Committee"
    ),
    "contact": Page("base:contact", "About", OVERVIEW, "OEP - Contact"),
    "privacy_policy": Page(
        "base:legal-privacy-policy", "About", OVERVIEW, "Privacy policy"
    ),
    "terms_of_use": Page("base:legal-tou", "About", OVERVIEW, "Terms of Use"),
    "faq": Page("base:faq", "About", OVERVIEW, "Frequently Asked Questions (FAQ)"),
    "discussion": Page("base:discussion", "About", OVERVIEW, "Discussion"),
    "project_detail": Page(
        "base:project_detail",
        "About",
        OVERVIEW,
        "open_eGo: open electricity grid optimization",
        kwargs={"project_id": "open_ego"},
    ),
    # The spec's worked row for the account pages (spec #2632, "Page header").
    "edit_profile": Page(
        "login:edit",
        "Account",
        (("Dashboard", "login:profile"), ("Settings", "login:settings")),
        "Update account profile",
        own=True,
    ),
}
# Text a page gains with its band that it did not carry before: the accepted
# page title of terms of use (spec #2632, from the footer link).
ACCEPTED = {"terms_of_use": "Terms of Use"}


def bands_of(root):
    return root.find_all("header", BAND)


def trail_items(band):
    nav = band.find("nav")
    ordered = nav.find("ol", TRAIL)
    return nav, ordered, ordered.elements


class ComponentTest(SimpleTestCase):
    """The include on its own."""

    def render(self, **context):
        return parse(render_to_string(COMPONENT, context))

    def test_the_title_is_the_one_h1_and_the_trails_current_item(self):
        root = self.render(
            area="About",
            icon="icons/area_about.html",
            crumb_label="Overview",
            crumb_url="/about/",
            title="A subject",
        )
        h1s = root.find_all("h1")
        self.assertEqual(len(h1s), 1)
        self.assertEqual(h1s[0].text(), "A subject")
        band = root.find("header", BAND)
        nav, ordered, items = trail_items(band)
        self.assertEqual(nav.attrs.get("aria-label"), "Breadcrumb")
        self.assertIs(h1s[0].parent, items[-1])
        self.assertEqual(items[-1].attrs.get("aria-current"), "page")
        self.assertTrue(all("aria-current" not in i.attrs for i in items[:-1]))

    def test_the_trail_holds_only_its_items(self):
        # The separator is the item before it drawing "/", so the list has no
        # separator of its own that a wrapped line could start with.
        root = self.render(
            area="Account",
            crumb_label="Dashboard",
            crumb_url="/a/",
            crumb2_label="Settings",
            crumb2_url="/b/",
            title="Here",
        )
        _nav, ordered, items = trail_items(root)
        self.assertEqual([i.tag for i in items], ["li", "li", "li"])
        loose_text = [c for c in ordered.children if isinstance(c, str) and c.strip()]
        self.assertEqual(loose_text, [])
        self.assertNotIn("/", ordered.text())
        links = ordered.find_all("a")
        self.assertEqual([a.text() for a in links], ["Dashboard", "Settings"])
        self.assertEqual([a.attrs["href"] for a in links], ["/a/", "/b/"])

    def test_the_area_line_carries_its_icon_and_label(self):
        root = self.render(area="About", icon="icons/area_about.html", title="X")
        area = root.find(css_class=AREA)
        self.assertEqual(area.text(), "About")
        icon = area.find("svg")
        self.assertIsNotNone(icon)
        self.assertEqual(icon.attrs.get("aria-hidden"), "true")
        self.assertIsNone(root.find("h1").find("a"))

    def test_a_trail_without_links_is_the_title_alone(self):
        root = self.render(area="About", title="Only me")
        _nav, _ordered, items = trail_items(root)
        self.assertEqual(len(items), 1)
        self.assertEqual(root.find("h1").text(), "Only me")

    def test_slots_render_only_when_given(self):
        bare = self.render(area="About", title="X")
        self.assertIsNone(bare.find(css_class="page-header__description"))
        self.assertIsNone(bare.find(css_class="page-header__actions"))
        self.assertNotIn("page-header--tabs", bare.find("header").classes)

        full = self.render(
            area="Styleguide",
            title="X",
            description="One muted line.",
            actions="styleguide/entries/_page_header_actions.html",
            # Any template fills the tabs slot; the house tab row is #2648's.
            tabs="icons/area_account.html",
        )
        band = full.find("header")
        self.assertEqual(
            band.find(css_class="page-header__description").text(), "One muted line."
        )
        actions = band.find(css_class="page-header__actions")
        self.assertTrue(actions.find_all("a"))
        self.assertIn("page-header--tabs", band.classes)
        self.assertIsNotNone(band.find(css_class="page-header__tabs").find("svg"))

    def test_an_example_has_no_h1(self):
        # The catalogue shows the band inside a page that has its own h1.
        root = self.render(area="About", title="Shown", as_example=True)
        self.assertEqual(root.find_all("h1"), [])
        _nav, _ordered, items = trail_items(root)
        self.assertEqual(items[-1].text(), "Shown")
        self.assertEqual(items[-1].attrs.get("aria-current"), "page")

    def test_the_title_is_escaped(self):
        root = self.render(area="About", title="<script>x</script>")
        self.assertEqual(root.find("h1").text(), "<script>x</script>")
        self.assertIsNone(root.find("script"))


class PagesWithABandTest(TestViewsTestCase):
    """The pages that started with a title glued under the navbar."""

    def kwargs(self, page):
        return {"user_id": self.user.pk} if page.own else page.kwargs

    def page(self, slug):
        page = PAGES[slug]
        response = self.get(
            page.view,
            kwargs=self.kwargs(page),
            logged_in=page.own,
            expect_status=200,
        )
        return parse(response.content.decode())

    def test_exactly_one_h1_inside_the_band_as_the_trails_last_part(self):
        for slug in PAGES:
            with self.subTest(page=slug):
                root = self.page(slug)
                bands = bands_of(root)
                self.assertEqual(len(bands), 1, "one band")
                h1s = root.find_all("h1")
                self.assertEqual(len(h1s), 1, "one h1")
                _nav, _ordered, items = trail_items(bands[0])
                self.assertIs(h1s[0].parent, items[-1])
                self.assertEqual(items[-1].attrs.get("aria-current"), "page")

    def test_area_trail_and_subject(self):
        for slug, page in PAGES.items():
            with self.subTest(page=slug):
                root = self.page(slug)
                band = bands_of(root)[0]
                self.assertEqual(band.find(css_class=AREA).text(), page.area)
                _nav, ordered, _items = trail_items(band)
                found = [(a.text(), a.attrs["href"]) for a in ordered.find_all("a")]
                kwargs = {"user_id": self.user.pk} if page.own else None
                expected = [
                    (label, reverse(view, kwargs=kwargs)) for label, view in page.links
                ]
                self.assertEqual(found, expected)
                self.assertLessEqual(len(found), 2, "at most two link levels")
                self.assertEqual(root.find("h1").text(), page.title)

    def test_the_about_areas_labels_are_the_navbars(self):
        # No new wording: the band's area and trail labels on these pages are
        # the navbar's own (its "About" menu and that menu's "Overview").
        for slug, page in PAGES.items():
            if page.area != "About":
                continue
            with self.subTest(page=slug):
                root = self.page(slug)
                navbar = {a.text() for a in root.find("nav", "navbar").find_all("a")}
                band = bands_of(root)[0]
                labels = [band.find(css_class=AREA).text()]
                labels += [a.text() for a in band.find("ol", TRAIL).find_all("a")]
                for label in labels:
                    self.assertIn(label, navbar)

    def test_the_band_sits_above_the_content_inside_main(self):
        for slug in PAGES:
            with self.subTest(page=slug):
                root = self.page(slug)
                main = root.find("main")
                band = bands_of(root)[0]
                self.assertIs(band.parent, main)
                content = root.find(css_class="content")
                self.assertLess(main.elements.index(band), main.elements.index(content))

    def test_texts_are_unchanged(self):
        def borrowed(node):
            # The area line and the trail's links repeat navbar and footer
            # labels, and an "On this page" list's links repeat the page's own
            # headings (#2649); everything else is the page's own text.
            in_trail = any(a.has_class(TRAIL) for a in node.ancestors)
            in_toc = any(a.has_class("toc__list") for a in node.ancestors)
            return node.has_class(AREA) or (node.tag == "a" and (in_trail or in_toc))

        for slug in PAGES:
            with self.subTest(page=slug):
                main = self.page(slug).find("main")
                before = (SNAPSHOTS / f"{slug}.txt").read_text().strip()
                expected = " ".join(filter(None, (ACCEPTED.get(slug), before)))
                self.assertEqual(main.text(skip=borrowed), expected)


class PagesWithoutABandTest(TestViewsTestCase):
    """Account pages keep their own heading; error pages have no header."""

    def assertNoBand(self, html):
        self.assertEqual(bands_of(parse(html)), [])

    def test_account_pages(self):
        for view in ("account_login", "account_signup", "account_reset_password"):
            with self.subTest(page=view):
                self.assertNoBand(self.get(view).content.decode())

    def test_a_missing_page(self):
        response = self.client.get("/no/such/page/")
        self.assertEqual(response.status_code, 404)
        self.assertNoBand(response.content.decode())

    @override_settings(DEBUG=False)
    def test_a_server_error(self):
        response = server_error(RequestFactory().get("/"))
        self.assertEqual(response.status_code, 500)
        self.assertNoBand(response.content.decode())
