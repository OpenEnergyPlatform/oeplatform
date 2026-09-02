"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re

from base.tests import TestViewsTestCase
from dataedit.models import Tag
from modelview.helper import getClasses
from modelview.tests.corpus import seed_corpus

#: One rendered checkbox per offered tag.
CHECKBOX = re.compile(r'id="select_([^"]+)"')


class TagFilterListTestCase(TestViewsTestCase):
    def sidebar_tags(self, sheettype, query=None):
        """The tag pks the sidebar offers, in render order."""
        resp = self.get(
            "modelview:modellist", kwargs={"sheettype": sheettype}, query=query
        )
        return CHECKBOX.findall(resp.content.decode("utf-8"))

    def tags_in_use(self, sheettype):
        cls, _ = getClasses(sheettype)
        return set(
            Tag.objects.filter(factsheets__in=cls.objects.all())
            .values_list("pk", flat=True)
            .distinct()
        )


class TestTheFilterListIsTheTagsInUse(TagFilterListTestCase):
    """The list must be O(distinct tags in use), not O(tag attachments).

    That is the durable part of this change. The corpus below makes the two
    diverge by a wide margin on purpose: three corrupted factsheets each carry
    the whole 260-tag vocabulary, so there are far more attachments than
    distinct tags, exactly as on production where 12,156 attachments cover 825
    distinct tags and the sidebar rendered a checkbox for every attachment.
    """

    @classmethod
    def setUpTestData(cls):
        cls.models = seed_corpus(sheettype="model", factsheets=20, corrupted=3)
        cls.frameworks = seed_corpus(sheettype="framework", factsheets=8, corrupted=1)

    def test_each_tag_in_use_is_offered_exactly_once(self):
        for sheettype in ("model", "framework"):
            with self.subTest(sheettype=sheettype):
                offered = self.sidebar_tags(sheettype)

                self.assertEqual(len(offered), len(set(offered)))
                self.assertEqual(set(offered), self.tags_in_use(sheettype))

    def test_the_list_is_not_proportional_to_tag_attachments(self):
        """The regression this permanently forecloses.

        Asserted as a bound rather than an equality so that it fails loudly if
        the list ever grows with attachments again, which is how the page went
        from 60 s to 400 s while the data barely changed.
        """
        offered = self.sidebar_tags("model")

        self.assertLess(len(offered), self.models.edges)
        self.assertEqual(len(offered), len(self.tags_in_use("model")))

    def test_no_tag_checkbox_is_pre_checked_without_a_filter(self):
        """A page with no filter in its URL has no tag selected.

        Today this holds for the wrong reason -- the conditional compares a pk
        against model instances and is always false. It must still hold once
        T5 makes the pre-check real.

        Scoped to the tag inputs on purpose: the Fields section of the same
        sidebar legitimately renders `checked` for the default columns, so a
        whole-page search would be asserting something else entirely.
        """
        resp = self.get("modelview:modellist", kwargs={"sheettype": "model"})
        body = resp.content.decode("utf-8")

        checked = [
            element.split(">")[0]
            for element in body.split("<input")
            if 'id="select_' in element.split(">")[0]
            and "checked" in element.split(">")[0]
        ]
        self.assertEqual(checked, [], msg=f"{len(checked)} tag checkboxes pre-checked")


class TestTheFilterListIsScopedPerSheetType(TagFilterListTestCase):
    """Unscoped, the frameworks page offered 290 tags where 71 were in use.

    219 of its checkboxes returned zero results when clicked. On the models
    page only 17 of 290 were spurious, which is why the defect hid: the page
    it broke is the one nobody measured.
    """

    @classmethod
    def setUpTestData(cls):
        cls.models = seed_corpus(sheettype="model", factsheets=6, corrupted=0)
        cls.frameworks = seed_corpus(sheettype="framework", factsheets=4, corrupted=0)
        # A tag attached to a framework and to no model at all.
        cls.framework_only = Tag.objects.create(
            name_normalized="framework-only", name="framework only", color=0x00FF00
        )
        cls.frameworks.factsheets[0].tags.add(cls.framework_only)
        cls.model_only = Tag.objects.create(
            name_normalized="model-only", name="model only", color=0xFF0000
        )
        cls.models.factsheets[0].tags.add(cls.model_only)

    def test_the_models_page_does_not_offer_a_framework_only_tag(self):
        offered = self.sidebar_tags("model")

        self.assertIn(self.model_only.pk, offered)
        self.assertNotIn(self.framework_only.pk, offered)

    def test_the_frameworks_page_does_not_offer_a_model_only_tag(self):
        offered = self.sidebar_tags("framework")

        self.assertIn(self.framework_only.pk, offered)
        self.assertNotIn(self.model_only.pk, offered)

    def test_a_tag_attached_to_nothing_is_offered_nowhere(self):
        unused = Tag.objects.create(
            name_normalized="unused-tag", name="unused tag", color=0x0000FF
        )

        for sheettype in ("model", "framework"):
            with self.subTest(sheettype=sheettype):
                self.assertNotIn(unused.pk, self.sidebar_tags(sheettype))


class TestTheFilterListIsOrderedByName(TagFilterListTestCase):
    """Ordered by name, so a tag can be found in a list of hundreds.

    Deliberately NOT by the tag model's `usage_count`: that field exists and
    looks apt, but it is incremented only by table search elsewhere in the
    platform and never by anything in this app, so ordering by it would rank
    an unrelated quantity.
    """

    @classmethod
    def setUpTestData(cls):
        cls.models = seed_corpus(sheettype="model", factsheets=4, corrupted=0)
        # Names deliberately out of step with the seeding order, so that
        # ordering by name is distinguishable from ordering by primary key.
        sheet = cls.models.factsheets[0]
        cls.renamed = []
        for pk_suffix, name in (("aaa", "zulu"), ("mmm", "alpha"), ("zzz", "mike")):
            tag = Tag.objects.create(
                name_normalized=f"order-{pk_suffix}", name=name, color=0x123456
            )
            sheet.tags.add(tag)
            cls.renamed.append(tag)

    def test_the_offered_tags_are_in_name_order(self):
        offered = self.sidebar_tags("model")
        by_pk = {t.pk: t.name for t in Tag.objects.filter(pk__in=offered)}

        names = [by_pk[pk] for pk in offered]
        self.assertEqual(names, sorted(names))

    def test_name_order_is_not_primary_key_order(self):
        """Guards the test above from passing by coincidence."""
        offered = self.sidebar_tags("model")
        renamed_pks = [t.pk for t in self.renamed]

        in_render_order = [pk for pk in offered if pk in renamed_pks]
        self.assertEqual(in_render_order, ["order-mmm", "order-zzz", "order-aaa"])
