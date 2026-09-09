"""Repair the Model/Framework factsheets the old tag editor corrupted.

Opening a factsheet for editing used to pre-check every tag on the platform,
so saving attached all of them. On production that hit **23 of 339 factsheets**
-- 21 models and 2 frameworks -- and those 23 hold **95% of every
factsheet->tag attachment in the database** (16,942 of 17,839). Repairing them
is therefore also the largest single load-time lever available: with no code
change at all it takes the list page from 33.45 s / 20.1 MB to 3.58 s / 7.1 MB.

**Do not run this against production until the editor's fix is deployed.** The
old editor re-corrupts on every save, at roughly two factsheets a month, so a
cleanup that runs first buys a few weeks and then has to be done again.

The repair is lossy and the loss is real: each of the 23 had some small unknown
number of legitimate tags among the ~825, and they are indistinguishable from
the damage. Across the 284 healthy model factsheets there are ~897 legitimate
attachments (about three each), so the 23 probably lose on the order of 60-70
real tags in total. That is why the JSON record exists, why the dry run is the
default, and why the public notice has to say so -- otherwise the zeros read as
"these models were never tagged".

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from dataedit.models import Tag
from modelview.models import CORRUPT_TAG_THRESHOLD, BasicFactsheet

#: Below the threshold but far above normal: printed, never touched.
#:
#: A quarter of the threshold, chosen as a rule rather than copied from the
#: census: the two the census names (106 and 73 tags) both clear it, but so
#: would anything else in that band, which is the point -- a human decides
#: them instead of the threshold skipping them in silence.
REVIEW_FLOOR = CORRUPT_TAG_THRESHOLD // 4


def sheettype_of(sheet):
    """Which kind of factsheet a `BasicFactsheet` row is.

    `Energymodel` and `Energyframework` are multi-table inheritance over this
    shared parent, so selecting over the parent catches both in one query --
    and a models-only sweep would miss the two corrupted frameworks.
    """
    if hasattr(sheet, "energymodel"):
        return "model"
    if hasattr(sheet, "energyframework"):
        return "framework"
    return "factsheet"


def date_generations(generations):
    """The window in which each of these generations was saved.

    A corrupted factsheet attached the *whole* tag table, so its tag count is
    that table's size at the moment it was saved -- a generation. Ordering the
    tags by `usage_tracked_since`, the Nth dates the moment the table reached N
    rows and the (N+1)th the moment it outgrew them, so the corrupting save
    happened somewhere in between.

    Both ends are reported, because they answer different halves of "is there
    a backup old enough". Anything older than the window certainly predates the
    save; anything inside it might, and needs checking. A generation equal to
    today's tag count has no upper end -- the table has not outgrown it yet --
    and quoting one would be a guess presented as a date.

    This is what makes recovery datable rather than guesswork: production's 23
    fall into eight generations, and a backup from March 2026 still recovers 15
    of the 21 models. Run this before asking anyone for backups.
    """
    stamps = list(
        Tag.objects.order_by("usage_tracked_since").values_list(
            "usage_tracked_since", flat=True
        )
    )
    dated = []
    for size in sorted(generations, reverse=True):
        inside_the_table = 0 < size <= len(stamps)
        dated.append(
            {
                "generation": size,
                "reached": stamps[size - 1] if inside_the_table else None,
                "outgrown": stamps[size] if size < len(stamps) else None,
            }
        )
    return dated


def _day(stamp, otherwise):
    return stamp.strftime("%Y-%m-%d") if stamp else otherwise


class Command(BaseCommand):
    help = (
        "Repair factsheets whose tags are a snapshot of the whole tag table. "
        "Prints what it would do unless --apply is given."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help=(
                "Actually remove the tags. Without it the command only "
                "reports, which is the default because the removal is "
                "irreversible and this app records no history."
            ),
        )
        parser.add_argument(
            "--record",
            default=None,
            help=(
                "Where to write the JSON record of what was removed. Written "
                "only by a real run. Defaults to "
                "factsheet-tag-repair-<timestamp>.json in the working "
                "directory."
            ),
        )

    def handle(self, *args, **options):
        apply = options["apply"]

        sheets = (
            BasicFactsheet.objects.annotate(tag_count=Count("tags"))
            .filter(tag_count__gt=REVIEW_FLOOR)
            .select_related("energymodel", "energyframework")
            .order_by("-tag_count", "pk")
        )
        selected = [s for s in sheets if s.tag_count > CORRUPT_TAG_THRESHOLD]
        borderline = [s for s in sheets if s.tag_count <= CORRUPT_TAG_THRESHOLD]
        generations = date_generations({s.tag_count for s in selected})

        self._report(selected, borderline, generations, apply)

        record = {
            "run_at": timezone.now().isoformat(),
            "threshold": CORRUPT_TAG_THRESHOLD,
            "applied": apply,
            "generations": generations,
            "factsheets": [],
        }

        for sheet in selected:
            removed = sorted(sheet.tags.values_list("pk", flat=True))
            record["factsheets"].append(
                {
                    "pk": sheet.pk,
                    "model_name": sheet.model_name,
                    "sheettype": sheettype_of(sheet),
                    "generation": sheet.tag_count,
                    "removed_tags": removed,
                }
            )

        if not apply:
            self.stdout.write(
                self.style.WARNING(
                    "\nThis was a dry run: nothing was changed and no record "
                    "was written. Re-run with --apply to repair."
                )
            )
            return

        path = Path(
            options["record"]
            or "factsheet-tag-repair-%s.json"
            % timezone.now().strftime("%Y%m%dT%H%M%SZ")
        )
        with transaction.atomic():
            # The record goes first, inside the transaction: if writing it
            # fails the removal rolls back. The other order can lose the tags
            # AND the only account of what they were, which is the one outcome
            # this command must not produce. A record without a repair is
            # harmless by comparison -- re-running writes the same one.
            path.write_text(json.dumps(record, indent=2, default=str))
            for sheet in selected:
                sheet.tags.clear()

        self.stdout.write(
            self.style.SUCCESS(
                "\nRepaired %d factsheet(s). Record written to %s -- keep it: "
                "this app records no history, so it is the only account of "
                "what these zeros replaced." % (len(selected), path)
            )
        )

    def _report(self, selected, borderline, generations, apply):
        self.stdout.write(
            "Selected %d factsheet(s) carrying more than %d tags%s"
            % (
                len(selected),
                CORRUPT_TAG_THRESHOLD,
                ", to be set to zero tags:" if apply else ":",
            )
        )
        self._write_rows(selected)

        if selected:
            self.stdout.write(
                "\nEach count above is a generation: the factsheet attached "
                "the whole tag table,\nso the count is that table's size at "
                "the moment it was saved. The save fell\nsomewhere in the "
                "window below. A backup from before the window certainly "
                "holds\nthe factsheet's real tags; one from inside it might, "
                "and has to be checked."
            )
            for dated in generations:
                self.stdout.write(
                    "  generation %5d: saved between %s and %s"
                    % (
                        dated["generation"],
                        _day(dated["reached"], "an unknown date"),
                        _day(
                            dated["outgrown"],
                            "today (the table has not " "outgrown that size)",
                        ),
                    )
                )

        if borderline:
            self.stdout.write(
                "\n%d factsheet(s) over %d tags but under the threshold -- not "
                "selected, review manually:" % (len(borderline), REVIEW_FLOOR)
            )
            self._write_rows(borderline)

    def _write_rows(self, sheets):
        for sheet in sheets:
            self.stdout.write(
                "  [%-9s] %-40s %5d tags"
                % (sheettype_of(sheet), sheet.model_name, sheet.tag_count)
            )
