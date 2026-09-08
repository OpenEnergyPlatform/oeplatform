"""The platform-wide tag pages: the overview and the create/edit form.

These two pages are one flow -- you reach the editor from the overview and you
come back to it -- but they were not built as one: the editor renders no page
header, its "Cancel" goes somewhere else entirely, and a rejected name bounces
the user to the overview with what they typed thrown away.

Underneath the layout complaint sits a sharper one. Tags are ONE vocabulary
shared by database tables and by Model/Framework factsheets, but these pages
only ever knew about tables: the editor asked `tag.tables` whether a tag was in
use, so a tag carrying 200 factsheets and no table reported itself unused.
Deleting it strips it from every one of them, and this app records no history.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

from django.urls import reverse

from base.tests import TestViewsTestCase
from dataedit.models import Tag
from modelview.tests.corpus import seed_corpus


class TagPageTestCase(TestViewsTestCase):

    @classmethod
    def make_tag(cls, name="Wind onshore", color=0x16AAD9):
        tag = Tag(name=name, color=color)
        tag.save()
        return tag

    def overview(self):
        return self.get("dataedit:tags", logged_in=True).content.decode("utf-8")

    def editor(self, tag=None):
        if tag is None:
            return self.get("dataedit:tags-new", logged_in=True).content.decode("utf-8")
        return self.get(
            "dataedit:tags-edit", kwargs={"tag_pk": tag.pk}, logged_in=True
        ).content.decode("utf-8")


class TestTheTwoPagesAreOneFlow(TagPageTestCase):
    """You arrive from the overview; you must be able to get back to it."""

    @classmethod
    def setUpTestData(cls):
        cls.tag = cls.make_tag()

    def test_the_overview_links_to_the_create_page(self):
        self.assertIn(reverse("dataedit:tags-new"), self.overview())

    def test_the_overview_links_to_each_tag_s_editor(self):
        self.assertIn(
            reverse("dataedit:tags-edit", kwargs={"tag_pk": self.tag.pk}),
            self.overview(),
        )

    def test_the_create_page_links_back_to_the_overview(self):
        """It used to offer "Cancel" straight out to the topic list, which is
        neither where the user came from nor anywhere near tags."""
        self.assertIn(reverse("dataedit:tags"), self.editor())

    def test_the_edit_page_links_back_to_the_overview(self):
        self.assertIn(reverse("dataedit:tags"), self.editor(self.tag))

    def test_both_pages_carry_a_page_header(self):
        """Every other page in this app has one; the editor had none, which is
        what made it look like it belonged to a different site."""
        for html in (self.overview(), self.editor(), self.editor(self.tag)):
            self.assertIn("main-header", html)

    def test_the_editor_says_which_of_the_two_things_it_is_doing(self):
        self.assertIn("Create Tag", self.editor())
        self.assertIn("Edit Tag", self.editor(self.tag))


class TestTheTagVocabularyIsShared(TagPageTestCase):
    """A tag in use by factsheets is in use, whatever the tables say.

    `Tag` is one model with two consumers -- `Table.tags` and
    `BasicFactsheet.tags` -- and the editor only ever asked the first.
    """

    @classmethod
    def setUpTestData(cls):
        cls.corpus = seed_corpus(sheettype="model", factsheets=2, corrupted=0)
        # Attached deliberately: the corpus spreads its own tags at random, and
        # its pks carry hyphens, which the tag URL pattern does not accept
        # (a real pk cannot -- `get_name_normalized` maps every non-alphanumeric
        # run to an underscore).
        cls.on_factsheets = cls.make_tag(name="On factsheets only")
        for sheet in cls.corpus.factsheets:
            sheet.tags.add(cls.on_factsheets)
        cls.unused = cls.make_tag(name="Nobody uses this")

    def test_a_tag_used_only_by_factsheets_counts_as_assigned(self):
        html = self.editor(self.on_factsheets)

        self.assertIn("factsheet", html.lower())
        self.assertNotIn("not assigned", html.lower())

    def test_an_unused_tag_says_so(self):
        self.assertIn("not assigned", self.editor(self.unused).lower())

    def test_the_editor_reports_how_many_factsheets_would_lose_the_tag(self):
        """A count, because "at least one object" is not enough to decide on."""
        expected = self.on_factsheets.factsheets.count()
        self.assertGreater(expected, 0)

        self.assertIn(str(expected), self.editor(self.on_factsheets))


class TestDeletingATag(TagPageTestCase):
    """Both halves were wrong, in opposite directions.

    The button was gated on an `is_admin` context variable no view ever passed,
    so it rendered for nobody -- not even an admin. The view behind it was
    gated on nothing but a login, so any account could delete any tag with a
    crafted POST, stripping it from every table and factsheet on the platform.
    """

    @classmethod
    def setUpTestData(cls):
        cls.corpus = seed_corpus(sheettype="model", factsheets=2, corrupted=0)

    def setUp(self):
        super().setUp()
        self.tag = self.make_tag(name="Delete me")

    def delete_it(self, logged_in=True, expect_status=None):
        return self.post(
            "dataedit:tags-set",
            data={"submit_delete": "Delete", "tag_id": self.tag.pk},
            logged_in=logged_in,
            expect_status=expect_status,
        )

    def test_a_non_admin_cannot_delete_a_tag(self):
        self.delete_it(expect_status=403)

        self.assertTrue(Tag.objects.filter(pk=self.tag.pk).exists())

    def test_an_admin_can_delete_a_tag(self):
        self.user.is_admin = True
        self.user.save()
        self.addCleanup(self._reset_admin)

        self.delete_it()

        self.assertFalse(Tag.objects.filter(pk=self.tag.pk).exists())

    def test_the_button_is_offered_to_an_admin(self):
        self.user.is_admin = True
        self.user.save()
        self.addCleanup(self._reset_admin)

        self.assertIn("submit_delete", self.editor(self.tag))

    def test_the_button_is_not_offered_to_a_non_admin(self):
        self.assertNotIn("submit_delete", self.editor(self.tag))

    def _reset_admin(self):
        self.user.is_admin = False
        self.user.save()


class TestSavingATag(TagPageTestCase):

    def test_a_valid_new_tag_lands_back_on_the_overview(self):
        resp = self.post(
            "dataedit:tags-set",
            data={
                "submit_save": "Save",
                "tag_text": "Fresh tag",
                "tag_color": "#16AAD9",
            },
            logged_in=True,
            expect_status=302,
        )

        self.assertEqual(resp["Location"], reverse("dataedit:tags"))
        self.assertTrue(Tag.objects.filter(name="Fresh tag").exists())

    def test_a_rejected_name_comes_back_with_what_was_typed(self):
        """It used to redirect to the overview, so the user lost their input
        and had to guess which of the two pages had complained."""
        self.make_tag(name="Taken")

        resp = self.post(
            "dataedit:tags-set",
            data={"submit_save": "Save", "tag_text": "Taken", "tag_color": "#FF0000"},
            logged_in=True,
            expect_status=200,
        )
        html = resp.content.decode("utf-8")

        self.assertTemplateUsed(resp, "dataedit/tag_editor.html")
        self.assertIn("Taken", html)
        self.assertIn("#FF0000", html)

    def test_an_existing_tag_can_be_renamed(self):
        tag = self.make_tag(name="Old name")

        self.post(
            "dataedit:tags-set",
            data={
                "submit_save": "Save",
                "tag_id": tag.pk,
                "tag_text": "New name",
                "tag_color": "#16AAD9",
            },
            logged_in=True,
            expect_status=302,
        )

        tag.refresh_from_db()
        self.assertEqual(tag.name, "New name")

    def test_a_rename_does_not_move_the_tag_s_identity(self):
        """A characterisation test: it records behaviour, it does not bless it.

        `Tag.save()` computes `name_normalized` only on create, so a rename
        changes the display name and leaves the primary key behind. That is
        the safe half -- moving the pk would break every assignment -- but it
        also means the normalised name goes stale, and `update_keywords_from_tags`
        writes exactly that stale value into a table's metadata keywords. Whoever
        reconciles the two should change this test on purpose.
        """
        tag = self.make_tag(name="Old name")

        self.post(
            "dataedit:tags-set",
            data={
                "submit_save": "Save",
                "tag_id": tag.pk,
                "tag_text": "New name",
                "tag_color": "#16AAD9",
            },
            logged_in=True,
            expect_status=302,
        )

        tag.refresh_from_db()
        self.assertEqual(tag.pk, "old_name")
        self.assertEqual(tag.name, "New name")

    def test_a_rejected_name_creates_nothing(self):
        self.make_tag(name="Taken")

        self.post(
            "dataedit:tags-set",
            data={"submit_save": "Save", "tag_text": "Taken", "tag_color": "#FF0000"},
            logged_in=True,
            expect_status=200,
        )

        self.assertEqual(Tag.objects.filter(name="Taken").count(), 1)


class TestATagWithAnUnusualKey(TagPageTestCase):
    """One odd primary key must not take the whole overview down.

    The overview reverses the edit route once per tag, so a single pk outside
    the route's character class raised `NoReverseMatch` and 500ed the page for
    everyone. Nothing renormalises a pk on the way in -- `migrate_tags2` copies
    `name_normalized` straight out of the OEDB -- so the route has to accept
    what the column accepts.
    """

    @classmethod
    def setUpTestData(cls):
        cls.odd = Tag(name_normalized="legacy-tag.v2", name="Legacy tag", color=1)
        cls.odd.save()
        cls.make_tag(name="Ordinary")

    def test_the_overview_still_renders(self):
        self.assertIn("Legacy tag", self.overview())

    def test_its_editor_is_reachable(self):
        self.assertIn("Legacy tag", self.editor(self.odd))


class TestCreatingATagCannotHijackAnExistingOne(TagPageTestCase):
    """A tag's primary key is its NORMALISED name, so two display names
    collide: "Wind Onshore" and "wind onshore" are both `wind_onshore`.

    `save()` on a model whose pk is already set and has no default makes
    Django try an UPDATE before an INSERT -- so creating the second one used
    to overwrite the first's display name and colour, keeping its every table
    and factsheet assignment, and raising nothing at all. The view's
    duplicate-name guard could not fire because there was no error.
    """

    @classmethod
    def setUpTestData(cls):
        cls.corpus = seed_corpus(sheettype="model", factsheets=2, corrupted=0)
        cls.existing = cls.make_tag(name="Wind onshore", color=0x16AAD9)
        cls.corpus.factsheets[0].tags.add(cls.existing)

    def create(self, name, color="#FF0000"):
        """Deliberately without a status assertion.

        The data assertions below have to hold whatever the view answers --
        an overwrite that reported success would still be an overwrite.
        """
        self.client.force_login(self.user)
        return self.client.post(
            reverse("dataedit:tags-set"),
            data={"submit_save": "Save", "tag_text": name, "tag_color": color},
        )

    def test_a_colliding_name_is_refused(self):
        resp = self.create("Wind Onshore")

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "dataedit/tag_editor.html")

    def test_the_existing_tag_keeps_its_name_and_colour(self):
        self.create("Wind Onshore")

        self.existing.refresh_from_db()
        self.assertEqual(self.existing.name, "Wind onshore")
        self.assertEqual(self.existing.color, 0x16AAD9)

    def test_the_existing_tag_keeps_its_assignments(self):
        self.create("Wind Onshore")

        self.assertEqual(self.existing.factsheets.count(), 1)

    def test_no_second_tag_is_created(self):
        self.create("Wind Onshore")

        self.assertEqual(Tag.objects.filter(pk="wind_onshore").count(), 1)


class TestTheHtmxPanel(TagPageTestCase):
    """The overview loads the editor in place; both URLs still answer alone.

    The panel is the common path, so it renders the same partial the
    standalone page includes -- one template, no second copy to drift.
    """

    HTMX = {"HTTP_HX_REQUEST": "true"}

    @classmethod
    def setUpTestData(cls):
        cls.tag = cls.make_tag(name="Wind onshore")

    def test_the_overview_offers_the_panel_and_the_targets(self):
        html = self.overview()

        self.assertIn('id="tag-manager"', html)
        self.assertIn("hx-get", html)

    def test_an_htmx_request_returns_the_fragment_alone(self):
        resp = self.client.get(reverse("dataedit:tags-new"), **self.HTMX)
        html = resp.content.decode("utf-8")

        self.assertTemplateUsed(resp, "dataedit/partials/tag_manager.html")
        self.assertTemplateUsed(resp, "dataedit/partials/tag_editor_form.html")
        self.assertNotIn("<html", html)

    def test_a_plain_request_still_returns_the_whole_page(self):
        resp = self.get("dataedit:tags-new", logged_in=True)

        self.assertTemplateUsed(resp, "dataedit/tag_editor.html")
        self.assertIn("<html", resp.content.decode("utf-8"))

    def test_a_successful_save_over_htmx_returns_the_fragment_not_a_page(self):
        """The bug this pins: a 302 is followed transparently by htmx, so
        answering a save with a redirect swapped the ENTIRE rendered site into
        the editor panel."""
        resp = self.client.post(
            reverse("dataedit:tags-set"),
            data={
                "submit_save": "Save",
                "tag_text": "Brand new",
                "tag_color": "#16AAD9",
            },
            **self.HTMX,
        )
        html = resp.content.decode("utf-8")

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "dataedit/partials/tag_manager.html")
        self.assertNotIn("<html", html)
        self.assertNotIn("<nav", html)
        # The new tag is in the list that came back, and the panel is closed.
        self.assertIn("Brand new", html)
        self.assertNotIn("submit_save", html)

    def test_a_delete_over_htmx_returns_the_fragment_not_a_page(self):
        self.user.is_admin = True
        self.user.save()
        self.addCleanup(self._reset_admin)

        resp = self.client.post(
            reverse("dataedit:tags-set"),
            data={"submit_delete": "Delete", "tag_id": self.tag.pk},
            **self.HTMX,
        )
        html = resp.content.decode("utf-8")

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "dataedit/partials/tag_manager.html")
        self.assertNotIn("<html", html)
        self.assertNotIn(self.tag.name, html)

    def _reset_admin(self):
        self.user.is_admin = False
        self.user.save()

    def test_cancel_over_htmx_closes_the_panel(self):
        resp = self.client.get(reverse("dataedit:tags"), **self.HTMX)
        html = resp.content.decode("utf-8")

        self.assertTemplateUsed(resp, "dataedit/partials/tag_manager.html")
        self.assertNotIn("<html", html)
        self.assertNotIn("submit_save", html)

    def test_a_rejected_save_over_htmx_returns_the_form_not_a_page(self):
        resp = self.client.post(
            reverse("dataedit:tags-set"),
            data={
                "submit_save": "Save",
                "tag_text": "Wind Onshore",
                "tag_color": "#FF0000",
            },
            **self.HTMX,
        )
        html = resp.content.decode("utf-8")

        self.assertTemplateUsed(resp, "dataedit/partials/tag_editor_form.html")
        self.assertNotIn("<html", html)
        self.assertIn("Wind Onshore", html)
        self.assertIn("submit_save", html)

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)


class TestTheOverviewList(TagPageTestCase):

    @classmethod
    def setUpTestData(cls):
        for name in ("Zinc", "Apple", "Mango"):
            cls.make_tag(name=name)

    def test_the_tags_are_listed_by_name(self):
        html = self.overview()

        positions = [html.index(">%s<" % name) for name in ("Apple", "Mango", "Zinc")]
        self.assertEqual(positions, sorted(positions))

    def test_the_list_is_a_list(self):
        """`<a>` straight inside `<ul>` is invalid, and the float/clear hacks
        that held it together broke the buttons below out of the flow."""
        html = self.overview()

        self.assertIn("<li", html)
        self.assertNotIn("float: left", html)
