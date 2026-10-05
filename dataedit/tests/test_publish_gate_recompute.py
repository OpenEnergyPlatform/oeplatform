"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The ``recompute_publish_gate`` command (#2560): it evaluates the Publish gate
for every Table, writes nothing without ``--apply``, and with it stores every
verdict, names the flags it found stale and leaves agreeing ones alone.
"""  # noqa: 501

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from dataedit.models import Table
from login.tests.test_tables_columns import NO_LICENSE, OPEN_LICENSE


class RecomputePublishGateTests(TestCase):
    def setUp(self):
        Table.objects.bulk_create(
            [
                Table(name="r_new_ok", oemetadata=OPEN_LICENSE),
                Table(name="r_new_bad", oemetadata=NO_LICENSE),
                Table(name="r_empty"),
                Table(name="r_sandbox", oemetadata=OPEN_LICENSE, is_sandbox=True),
                Table(name="r_agrees", oemetadata=OPEN_LICENSE, publishable=True),
                Table(name="r_stale_pass", oemetadata=NO_LICENSE, publishable=True),
                Table(name="r_stale_fail", oemetadata=OPEN_LICENSE, publishable=False),
            ]
        )

    def run_command(self, *args):
        out = StringIO()
        call_command("recompute_publish_gate", *args, stdout=out)
        return out.getvalue()

    def stored(self):
        return dict(Table.objects.values_list("name", "publishable"))

    def test_a_dry_run_writes_nothing_and_says_what_it_would_change(self):
        before = self.stored()
        output = self.run_command()
        self.assertEqual(self.stored(), before)
        self.assertIn(
            "Evaluated 7 table(s) against the Publish gate (License).", output
        )
        self.assertIn("unknown -> publishable: 2", output)
        self.assertIn("unknown -> not publishable: 2", output)
        self.assertIn("not publishable -> publishable: 1", output)
        self.assertIn("publishable -> not publishable: 1", output)
        self.assertIn("unchanged: 1", output)
        self.assertIn("Dry run, nothing was written.", output)

    def test_apply_stores_every_verdict_sandbox_tables_included(self):
        self.run_command("--apply")
        self.assertEqual(
            self.stored(),
            {
                "r_new_ok": True,
                "r_new_bad": False,
                "r_empty": False,
                "r_sandbox": True,
                "r_agrees": True,
                "r_stale_pass": False,
                "r_stale_fail": True,
            },
        )

    def test_flags_that_were_set_and_wrong_are_named(self):
        output = self.run_command("--apply")
        self.assertIn("was stale: r_stale_fail", output)
        self.assertIn("was stale: r_stale_pass", output)
        self.assertNotIn("was stale: r_new_ok", output)
        self.assertIn("Wrote 6 verdict(s).", output)

    def test_a_second_run_finds_nothing_to_change(self):
        self.run_command("--apply")
        output = self.run_command("--apply")
        self.assertIn("unchanged: 7", output)
        self.assertIn("Wrote 0 verdict(s).", output)
        self.assertNotIn("->", output)
