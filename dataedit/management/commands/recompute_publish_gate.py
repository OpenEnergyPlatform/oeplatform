"""Recompute the stored Publish gate verdict (``Table.publishable``) for every
Table.

The metadata write path (``api.actions.set_table_metadata``) keeps the flag
current from then on; this command is for the cases it cannot cover:

- the deploy that adds the field, after which every flag is NULL;
- any deploy that changes ``dataedit.publish_gate.PUBLISH_GATE``, after which
  every stored flag was computed without the new check;
- repairing flags left stale by a metadata write past that path, which the
  profile dashboard reports as a ``publish_gate_disagreement`` warning.

Prints what it would change unless ``--apply`` is given. With ``--apply`` the
Tables are read under a row lock, so a metadata write arriving during the run
waits rather than having its fresh verdict overwritten by a stale one. Every
Table is evaluated, sandbox ones included. It writes only the flag: nothing a
user sees changes but the Publishable filter and sort.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from dataedit.models import Table
from dataedit.publish_gate import PUBLISH_GATE, is_publishable

#: How many changed Tables a run names before it only counts the rest.
NAMES_SHOWN = 20

#: Every change a run can make, in the order it reports them.
TRANSITIONS = ((None, True), (None, False), (False, True), (True, False))


def _word(value):
    return {True: "publishable", False: "not publishable", None: "unknown"}[value]


class Command(BaseCommand):
    help = (
        "Evaluate the Publish gate for every Table and store the verdict in "
        "Table.publishable. Prints what it would change unless --apply is given."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write the verdicts. Without it nothing is written.",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        checks = ", ".join(check.name for check in PUBLISH_GATE)
        if apply:
            with transaction.atomic():
                tables = Table.objects.select_for_update()
                changes, total = self._evaluate(tables)
                for value in (True, False):
                    ids = [pk for pk, (_, new, _) in changes.items() if new is value]
                    if ids:
                        Table.objects.filter(pk__in=ids).update(publishable=value)
        else:
            changes, total = self._evaluate(Table.objects.all())

        self.stdout.write(
            f"Evaluated {total:,} table(s) against the Publish gate ({checks})."
        )
        transitions = Counter((old, new) for old, new, _ in changes.values())
        for old, new in TRANSITIONS:
            if transitions[old, new]:
                count = transitions[old, new]
                self.stdout.write(f"  {_word(old)} -> {_word(new)}: {count:,}")
        self.stdout.write(f"  unchanged: {total - len(changes):,}")

        # A flag that was set and is now wrong was left stale by a metadata
        # write past the one path, or by a change to the gate: worth naming.
        flipped = sorted(name for old, _, name in changes.values() if old is not None)
        for name in flipped[:NAMES_SHOWN]:
            self.stdout.write(f"  was stale: {name}")
        if len(flipped) > NAMES_SHOWN:
            self.stdout.write(f"  ... and {len(flipped) - NAMES_SHOWN:,} more")

        if apply:
            self.stdout.write(f"Wrote {len(changes):,} verdict(s).")
        else:
            self.stdout.write("Dry run, nothing was written. Re-run with --apply.")

    def _evaluate(self, tables):
        """``{pk: (stored, verdict, name)}`` for every Table whose stored
        verdict differs from the gate's, and how many were evaluated."""
        changes, total = {}, 0
        for table in (
            tables.only("pk", "name", "oemetadata", "publishable")
            .order_by("pk")
            .iterator(chunk_size=500)
        ):
            total += 1
            verdict = is_publishable(table)
            if table.publishable is not verdict:
                changes[table.pk] = (table.publishable, verdict, table.name)
        return changes, total
