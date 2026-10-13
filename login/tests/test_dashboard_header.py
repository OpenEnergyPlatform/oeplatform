"""The dashboard's one header and Settings as the account page (#2653).

Every dashboard tab extends the profile shell, which draws the page header
once: area "Dashboard", the user's name as the h1, the four tabs on the
band's lower edge and a gear aside link to Settings. Settings is not a tab: it
has its own header (Account / Dashboard / Settings), a column of cards, no
tabs and no profile sidebar.
"""

from django.urls import reverse

from base.tests import TestViewsTestCase
from base.tests.html_tree import parse
from base.tests.test_page_header import AREA, bands_of, trail_items
from base.tests.test_tabs_and_dropdowns import asides, classes, tab_rows, tabs

DASHBOARD = ("profile", "datasets", "tables", "reviews", "organizations")
TAB_LABELS = ["Datasets", "Tables", "Reviews Early Access", "Organizations"]


class DashboardHeaderTest(TestViewsTestCase):
    def html(self, name):
        return self.get(
            f"login:{name}",
            kwargs={"user_id": self.user.pk},
            logged_in=True,
            expect_status=200,
        ).content.decode()

    def settings_url(self):
        return reverse("login:settings", kwargs={"user_id": self.user.pk})

    def test_every_tab_has_one_header_naming_the_user(self):
        for name in DASHBOARD:
            with self.subTest(page=name):
                root = parse(self.html(name))
                bands = bands_of(root)
                self.assertEqual(len(bands), 1)
                self.assertEqual(bands[0].find(css_class=AREA).text(), "Dashboard")
                _nav, ordered, items = trail_items(bands[0])
                self.assertEqual(ordered.find_all("a"), [])
                self.assertEqual(len(root.find_all("h1")), 1)
                self.assertIs(root.find("h1").parent, items[-1])
                self.assertEqual(root.find("h1").text(), self.user.name)

    def test_the_tabs_sit_in_the_header_once_and_settings_is_not_one(self):
        for name in DASHBOARD:
            with self.subTest(page=name):
                html = self.html(name)
                rows = tab_rows(html)
                self.assertEqual(len(rows), 1, "one tab row")
                band = bands_of(parse(html))[0]
                self.assertEqual(len(band.find_all("nav", "tabs")), 1, "in the header")
                labels = [
                    t.text() for t in band.find("nav", "tabs").find_all("a", "nav-link")
                ]
                self.assertEqual(labels, TAB_LABELS)
                self.assertNotIn(
                    f'href="{self.settings_url()}"', "".join(tabs(rows[0]))
                )

    def test_the_gear_is_the_rows_aside_link_to_settings(self):
        for name in DASHBOARD:
            with self.subTest(page=name):
                gear = asides(tab_rows(self.html(name))[0])
                self.assertEqual(len(gear), 1)
                self.assertIn(f'href="{self.settings_url()}"', gear[0])
                self.assertIn('aria-label="Settings"', gear[0])
                self.assertNotIn("active", classes(gear[0]))

    def test_the_gear_and_the_user_menu_both_reach_settings(self):
        root = parse(self.html("tables"))
        menu = [
            a
            for a in root.find("nav", "navbar").find_all("a")
            if a.attrs.get("href", "").strip() == self.settings_url()
        ]
        gear = root.find("a", "tabs__aside")
        self.assertEqual(len(menu), 1)
        self.assertEqual(gear.attrs["href"], self.settings_url())

        page = parse(self.html("settings"))
        self.assertEqual(page.find("h1").text(), "Settings")


class SettingsPageTest(TestViewsTestCase):
    def root(self):
        response = self.get(
            "login:settings",
            kwargs={"user_id": self.user.pk},
            logged_in=True,
            expect_status=200,
        )
        return parse(response.content.decode())

    def test_the_account_header_leads_back_to_the_dashboard(self):
        root = self.root()
        bands = bands_of(root)
        self.assertEqual(len(bands), 1)
        self.assertEqual(bands[0].find(css_class=AREA).text(), "Account")
        _nav, ordered, items = trail_items(bands[0])
        links = [(a.text(), a.attrs["href"]) for a in ordered.find_all("a")]
        profile = reverse("login:profile", kwargs={"user_id": self.user.pk})
        self.assertEqual(links, [("Dashboard", profile)])
        self.assertEqual(len(root.find_all("h1")), 1)
        self.assertIs(root.find("h1").parent, items[-1])
        self.assertEqual(root.find("h1").text(), "Settings")

    def test_no_tabs_and_no_profile_sidebar(self):
        root = self.root()
        self.assertIsNone(root.find(css_class="tabs"))
        self.assertIsNone(root.find(css_class="content__side"))
        self.assertIsNone(root.find(css_class="profile-sidebar"))

    def test_a_column_of_cards(self):
        column = self.root().find(css_class="account-cards")
        titles = [h.text() for h in column.find_all("h2", "card-title")]
        self.assertEqual(titles, ["Your Security Information", "Manage Profile"])
        for card in column.elements:
            self.assertTrue(card.has_class("card"))

    def test_reset_token_asks_the_confirm_dialog_first(self):
        url = reverse("login:reset-token")
        buttons = [
            b for b in self.root().find_all("button") if b.attrs.get("hx-post") == url
        ]
        self.assertEqual(len(buttons), 1)
        attrs = buttons[0].attrs
        self.assertTrue(attrs.get("hx-confirm"))
        self.assertEqual(attrs.get("data-confirm-title"), "Reset your API token?")
        self.assertEqual(attrs.get("data-confirm-verb"), "Reset token")
        self.assertIn("data-confirm-danger", attrs)
