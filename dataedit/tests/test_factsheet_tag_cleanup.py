"""The command that repairs what the old factsheet tag editor did.

On production 23 of 339 factsheets carry a snapshot of the whole tag table --
21 models and 2 frameworks -- and **95% of every factsheet->tag attachment on
the platform (16,942 of 17,839) is that damage**. Repairing it is also the
single largest load-time lever the map found: with no code change at all it
takes the list page from 33.45 s / 20.1 MB to 3.58 s / 7.1 MB.

The command is code-only. Running it against production is gated on the tag
editor's fix being deployed -- today's editor re-corrupts on every save, so
cleaning first buys a few weeks and then needs doing again.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

import json
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from dataedit.management.commands.repair_factsheet_tags import REVIEW_FLOOR
from dataedit.models import Tag
from modelview.models import CORRUPT_TAG_THRESHOLD, BasicFactsheet
from modelview.tests.corpus import seed_corpus


class CleanupTestCase(TestCase):
    """One corpus, one way to run the command."""

    def run_command(self, *args, **options):
        """Run the command, never letting it write into the working directory.

        A real run with no `--record` writes its record beside `manage.py`,
        which is right for an operator and litter in a test -- so unless a
        test names a path, it gets a throwaway one.
        """
        options.setdefault("record", str(self.scratch() / "record.json"))
        out = StringIO()
        call_command("repair_factsheet_tags", *args, stdout=out, stderr=out, **options)
        return out.getvalue()

    def scratch(self):
        """A directory that disappears with the test."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def over_threshold(self):
        return [
            sheet
            for sheet in BasicFactsheet.objects.all()
            if sheet.tags.count() > CORRUPT_TAG_THRESHOLD
        ]


class TestTheDryRunChangesNothing(CleanupTestCase):
    """The default, because the loss this command inflicts is irreversible.

    Each of the 23 had some small unknown number of legitimate tags among the
    ~825, and they are indistinguishable -- so a real run destroys on the order
    of 60-70 real attachments along with the damage.
    """

    @classmethod
    def setUpTestData(cls):
        cls.models = seed_corpus(sheettype="model", factsheets=5, corrupted=2)
        cls.frameworks = seed_corpus(sheettype="framework", factsheets=3, corrupted=1)

    def test_it_is_the_default(self):
        self.run_command()

        for sheet in self.models.corrupted + self.frameworks.corrupted:
            self.assertGreater(sheet.tags.count(), CORRUPT_TAG_THRESHOLD)

    def test_it_names_every_selected_factsheet_with_its_tag_count(self):
        output = self.run_command()

        for sheet in self.models.corrupted + self.frameworks.corrupted:
            self.assertIn(sheet.model_name, output)
        self.assertIn(str(len(self.models.tags)), output)

    def test_it_says_it_changed_nothing(self):
        output = self.run_command()

        self.assertIn("dry run", output.lower())

    def test_it_writes_no_record(self):
        record = self.scratch() / "record.json"

        self.run_command(record=str(record))

        self.assertFalse(record.exists())


class TestARealRun(CleanupTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.models = seed_corpus(sheettype="model", factsheets=5, corrupted=2)
        cls.frameworks = seed_corpus(sheettype="framework", factsheets=3, corrupted=1)

    def test_it_sets_the_selected_factsheets_to_zero_tags(self):
        self.run_command(apply=True)

        for sheet in self.models.corrupted + self.frameworks.corrupted:
            self.assertEqual(sheet.tags.count(), 0, msg=sheet.model_name)

    def test_it_covers_both_sheet_types(self):
        """A models-only sweep misses the two corrupted frameworks."""
        self.run_command(apply=True)

        self.assertEqual(self.frameworks.corrupted[0].tags.count(), 0)

    def test_no_factsheet_is_left_over_the_threshold(self):
        self.run_command(apply=True)

        self.assertEqual(self.over_threshold(), [])

    def test_it_leaves_healthy_factsheets_alone(self):
        before = {
            sheet.pk: set(sheet.tags.values_list("pk", flat=True))
            for sheet in self.models.healthy + self.frameworks.healthy
        }

        self.run_command(apply=True)

        for sheet in self.models.healthy + self.frameworks.healthy:
            self.assertEqual(
                set(sheet.tags.values_list("pk", flat=True)),
                before[sheet.pk],
                msg=sheet.model_name,
            )

    def test_it_is_safe_to_run_twice(self):
        self.run_command(apply=True)

        output = self.run_command(apply=True)

        self.assertEqual(self.over_threshold(), [])
        self.assertIn("Selected 0 factsheet", output)


class TestTheBorderlineFactsheets(CleanupTestCase):
    """The threshold must not skip anything silently.

    Production's distribution is bimodal with a factor-6.6 gap -- healthy tops
    out at 106 tags, corrupted start at 696 -- so the two heaviest healthy
    factsheets (106 and 73) sit far below the line but well above normal, and a
    human decides them rather than the threshold.
    """

    @classmethod
    def setUpTestData(cls):
        corpus = seed_corpus(sheettype="model", factsheets=4, corrupted=1)
        cls.borderline = corpus.healthy[0]
        cls.borderline.tags.add(*corpus.tags[: REVIEW_FLOOR + 10])
        cls.ordinary = corpus.healthy[1]

    def test_it_prints_them_for_manual_review(self):
        output = self.run_command()

        self.assertIn(self.borderline.model_name, output)
        self.assertIn("review manually", output)

    def test_it_does_not_print_an_ordinary_factsheet_for_review(self):
        output = self.run_command()

        self.assertNotIn(self.ordinary.model_name, output)

    def test_a_real_run_leaves_them_alone(self):
        count = self.borderline.tags.count()

        self.run_command(apply=True)

        self.assertEqual(self.borderline.tags.count(), count)


class TestTheJsonRecord(CleanupTestCase):
    """The only audit trail this operation will ever have.

    `modelview` records no history of any kind, so without this file there is
    no way to tell later what a factsheet's zero replaced -- and no way to
    check a backup restore against what was actually removed.
    """

    @classmethod
    def setUpTestData(cls):
        cls.corpus = seed_corpus(sheettype="model", factsheets=4, corrupted=2)

    def record_of_a_run(self):
        path = self.scratch() / "record.json"

        self.run_command(apply=True, record=str(path))

        return json.loads(path.read_text())

    def test_it_names_every_repaired_factsheet(self):
        record = self.record_of_a_run()

        names = {entry["model_name"] for entry in record["factsheets"]}
        self.assertEqual(names, {sheet.model_name for sheet in self.corpus.corrupted})

    def test_it_lists_exactly_the_tags_it_removed(self):
        removed_from = {
            sheet.pk: set(sheet.tags.values_list("pk", flat=True))
            for sheet in self.corpus.corrupted
        }

        record = self.record_of_a_run()

        for entry in record["factsheets"]:
            self.assertEqual(
                set(entry["removed_tags"]), removed_from[entry["pk"]], msg=entry["pk"]
            )

    def test_it_records_the_sheet_type(self):
        record = self.record_of_a_run()

        self.assertEqual({e["sheettype"] for e in record["factsheets"]}, {"model"})

    def test_it_records_when_the_run_happened_and_what_it_selected_on(self):
        record = self.record_of_a_run()

        self.assertIn("run_at", record)
        self.assertEqual(record["threshold"], CORRUPT_TAG_THRESHOLD)


class TestTheGenerations(CleanupTestCase):
    """A corrupted factsheet's tag count dates the save that corrupted it.

    It attached the whole tag table, so the count IS the size of that table at
    that moment. Production's 23 fall into eight such generations (825, 818,
    817, 816, 812, 807, 785, 696), which is why recovery is dated rather than
    guessed: a backup need only predate the generation you want, and one from
    March 2026 still recovers 15 of the 21 models.
    """

    @classmethod
    def setUpTestData(cls):
        cls.corpus = seed_corpus(sheettype="model", factsheets=4, corrupted=2)
        # Two generations: one factsheet saved before the last ten tags existed.
        cls.older = cls.corpus.corrupted[0]
        cls.older.tags.remove(*cls.corpus.tags[-10:])

        # Date the vocabulary, as production's does: the tag table grew over
        # time, so the Nth tag by tracking date says when it reached N rows.
        now = timezone.now()
        for position, tag in enumerate(cls.corpus.tags):
            Tag.objects.filter(pk=tag.pk).update(
                usage_tracked_since=now - timezone.timedelta(days=400 - position)
            )

    def test_it_reports_a_generation_per_selected_factsheet(self):
        output = self.run_command()

        self.assertIn(str(len(self.corpus.tags)), output)
        self.assertIn(str(len(self.corpus.tags) - 10), output)

    def test_it_dates_each_generation(self):
        """So "is there a backup old enough" is answerable per generation."""
        output = self.run_command()

        self.assertIn("generation", output.lower())
        for generation in (len(self.corpus.tags), len(self.corpus.tags) - 10):
            nth = Tag.objects.order_by("usage_tracked_since")[generation - 1]
            self.assertIn(nth.usage_tracked_since.strftime("%Y-%m-%d"), output)

    def test_it_dates_both_ends_of_the_window(self):
        """The save fell between the two, and only the older end is safe.

        Reporting the older end alone would reject every backup taken inside
        the window, some of which do predate the save.
        """
        generation = len(self.corpus.tags) - 10
        stamps = Tag.objects.order_by("usage_tracked_since").values_list(
            "usage_tracked_since", flat=True
        )

        output = self.run_command()

        self.assertIn(
            "saved between %s and %s"
            % (
                stamps[generation - 1].strftime("%Y-%m-%d"),
                stamps[generation].strftime("%Y-%m-%d"),
            ),
            output,
        )

    def test_the_current_generation_has_no_upper_end(self):
        """A factsheet corrupted at today's tag count could have been saved at
        any time since. Quoting a date there would be a guess in a date's
        clothing."""
        output = self.run_command()

        self.assertIn("today (the table has not outgrown that size)", output)

    def test_the_dating_survives_a_real_run(self):
        """The record keeps it: after the run the counts are gone."""
        path = self.scratch() / "record.json"

        self.run_command(apply=True, record=str(path))

        record = json.loads(path.read_text())
        generations = {entry["generation"] for entry in record["factsheets"]}
        self.assertEqual(
            generations, {len(self.corpus.tags), len(self.corpus.tags) - 10}
        )
        self.assertTrue(record["generations"])


class TestTheRecordIsWrittenBeforeTheTagsGo(CleanupTestCase):
    """The one outcome this command must never produce.

    Removing the tags and then failing to write the record would destroy the
    data and the only account of what it was in the same breath. A record
    without a repair is harmless by comparison -- re-running writes the same
    one -- so the write goes first, inside the transaction.
    """

    @classmethod
    def setUpTestData(cls):
        cls.corpus = seed_corpus(sheettype="model", factsheets=3, corrupted=1)

    def test_an_unwritable_record_leaves_the_tags_alone(self):
        before = self.corpus.corrupted[0].tags.count()

        with self.assertRaises(OSError):
            self.run_command(apply=True, record="/nonexistent-dir/record.json")

        self.assertEqual(self.corpus.corrupted[0].tags.count(), before)


class TestAnUnaffectedPlatform(CleanupTestCase):
    """The state the command leaves behind, and must tolerate finding."""

    @classmethod
    def setUpTestData(cls):
        seed_corpus(sheettype="model", factsheets=3, corrupted=0)

    def test_it_selects_nothing_and_says_so(self):
        output = self.run_command()

        self.assertIn("Selected 0 factsheet", output)
        self.assertNotIn("review manually", output)

    def test_a_real_run_on_a_clean_platform_writes_a_record_of_nothing(self):
        path = self.scratch() / "record.json"

        self.run_command(apply=True, record=str(path))

        self.assertEqual(json.loads(path.read_text())["factsheets"], [])
