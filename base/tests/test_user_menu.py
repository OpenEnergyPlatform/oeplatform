"""The navbar's user menu (#2644, spec #2632 "Navbar user menu").

Signed in, one menu under the user's name holds Dashboard, Settings and Sign
out, and below lg the same items are a section of the collapsed menu. Signed
out, Sign in is a nav link and Sign up the bar's one light button. No coloured
button is left in the navbar, and clicking one's own name opens the menu
instead of going to Settings.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re

from django.test import override_settings
from django.urls import reverse

from base.tests import TestViewsTestCase
from modelview.tests.html import elements_with_class, text

#: Pages in two shells: the homepage (base.html) and a dashboard tab
#: (base-profile.html). Every shell includes the same navbar.
PAGES = (("base:home", {}), ("login:organizations", {"user_id": None}))


class UserMenuTest(TestViewsTestCase):
    def pages(self, logged_in):
        for name, kwargs in PAGES:
            if "user_id" in kwargs:
                if not logged_in:
                    continue
                kwargs = {"user_id": self.user.pk}
            with self.subTest(page=name):
                yield self.get(
                    name, kwargs=kwargs, logged_in=logged_in
                ).content.decode()

    def corner(self, html):
        """The navbar's user area: the one user menu on the page."""
        navbars = elements_with_class(html, "index-navbar")
        self.assertEqual(len(navbars), 1)
        corners = elements_with_class(navbars[0], "user-menu")
        self.assertEqual(len(corners), 1)
        return navbars[0], corners[0]

    def test_signed_in_one_menu_holds_dashboard_settings_and_sign_out(self):
        dashboard = reverse("login:profile", args=[self.user.pk])
        settings = reverse("login:settings", args=[self.user.pk])
        for html in self.pages(logged_in=True):
            _, corner = self.corner(html)
            [menu] = elements_with_class(corner, "dropdown")
            toggle = re.search(r'<a\b[^>]*id="navbarDropdownUser"[^>]*>', menu)
            self.assertIsNotNone(toggle)
            self.assertIn('data-bs-toggle="dropdown"', toggle.group(0))
            # Behaviour change: one's own name opens the menu, not Settings.
            self.assertIn('href="#"', toggle.group(0))
            self.assertIn(self.user.name, text(menu))

            [items] = elements_with_class(menu, "dropdown-menu")
            order = [
                items.index(f'href="{dashboard}"'),
                items.index(f'href="{settings}"'),
                items.index('class="dropdown-divider"'),
                items.index(">Sign out</button>"),
            ]
            self.assertEqual(order, sorted(order))
            self.assertEqual(
                [text(item) for item in elements_with_class(items, "dropdown-item")],
                ["Dashboard", "Settings", "Sign out"],
            )

    def test_sign_out_is_a_form_posting_to_allauth(self):
        logout = reverse("account_logout")
        for html in self.pages(logged_in=True):
            _, corner = self.corner(html)
            forms = re.findall(r"<form\b[^>]*>.*?</form>", corner, re.S)
            # one in the menu, one in the phone section
            self.assertEqual(len(forms), 2)
            for form in forms:
                self.assertIn('method="post"', form)
                self.assertIn(f'action="{logout}"', form)
                self.assertIn('name="csrfmiddlewaretoken"', form)
                self.assertRegex(form, r'<button type="submit"[^>]*>Sign out</button>')

    def test_the_sign_out_form_signs_out(self):
        self.client.force_login(self.user)

        self.client.post(reverse("account_logout"))

        home = self.client.get(reverse("base:home")).content.decode()
        self.assertIn(">Sign in</a>", self.corner(home)[1])

    def test_below_lg_the_same_items_are_a_section_of_the_collapsed_menu(self):
        for html in self.pages(logged_in=True):
            navbar, corner = self.corner(html)
            # inside the collapse, so the bar itself keeps one row on a phone
            [collapse] = elements_with_class(navbar, "navbar-collapse")
            self.assertIn(corner, collapse)
            section = elements_with_class(corner, "d-lg-none")
            self.assertEqual(
                [text(item) for item in section],
                [self.user.name, "Dashboard", "Settings", "Sign out"],
            )
            [menu] = elements_with_class(corner, "dropdown")
            self.assertIn("d-none d-lg-block", menu)

    def test_signed_in_the_navbar_has_no_button_at_all(self):
        for html in self.pages(logged_in=True):
            navbar, _ = self.corner(html)
            self.assertNotRegex(navbar, r'class="(?:[^"]* )?btn(?: [^"]*)?"')

    def test_signed_out_sign_in_is_a_link_and_sign_up_the_light_button(self):
        for html in self.pages(logged_in=False):
            navbar, corner = self.corner(html)
            sign_in = re.search(r"<a\b[^>]*>Sign in</a>", corner).group(0)
            self.assertIn('class="nav-link"', sign_in)
            self.assertIn(f'href="{reverse("account_login")}"', sign_in)
            sign_up = re.search(r"<a\b[^>]*>Sign up</a>", corner, re.S).group(0)
            self.assertIn("btn btn-on-strong", sign_up)
            self.assertIn(f'href="{reverse("account_signup")}"', sign_up)
            # the bar's one button
            self.assertEqual(len(re.findall(r'class="btn\b', navbar)), 1)

    @override_settings(ACCOUNT_ALLOW_REGISTRATION=False)
    def test_without_registration_there_is_no_sign_up(self):
        for html in self.pages(logged_in=False):
            _, corner = self.corner(html)
            self.assertIn(">Sign in</a>", corner)
            self.assertNotIn("Sign up", corner)


class CatalogueEntryTest(TestViewsTestCase):
    def test_the_entry_shows_both_corners_beside_the_readers_own(self):
        html = self.get("base:styleguide", logged_in=True).content.decode()

        entry = html.split('data-entry="user_menu"', 1)[1].split("data-entry=", 1)[0]
        self.assertIn("Ada Lovelace", entry)
        self.assertIn(">Sign up</a>", entry)
        # the reader's own menu and the example's keep their ids apart
        self.assertEqual(html.count('id="navbarDropdownUser"'), 1)
        self.assertEqual(html.count('id="catalogueUserMenu"'), 1)
