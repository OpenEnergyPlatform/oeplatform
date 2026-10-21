"""Backfill the data half of the Modified date (``Table.data_modified``) for
Tables whose rows changed before the field was stamped (#2558).

Two records survive from before that release, and the date is the later of
them:

- the Edit Journal: the latest *applied* change in the Table's three Journal
  Tables (``_<schema>._<name>_insert``/``_edit``/``_delete`` in the OEDB). A
  change still waiting for Apply never reached the Main Table, so it does not
  count;
- the latest successful Bulk Load Event for the Table.

A Table with neither keeps NULL. The metadata half (``metadata_modified``) is
never written: no metadata save was ever timestamped, so there is nothing to
recover. ``date_updated`` is not a source either: for Tables older than
2025-10-29 it holds a date copied out of their metadata.

**Only a NULL is ever filled.** Every write after the release stamps the
application's clock at the moment of the change, which is later than anything
recovered here. So a Table that already has a date keeps it, whether a write
stamped it or an earlier run of this command did. The test sits in the
UPDATE's own WHERE clause, so a stamp landing during the run wins too. That
makes the command safe to re-run: a second run finds nothing to fill.

**The OEDB is read, never written.** The reads run in READ ONLY transactions,
one per chunk of journals. The journals are found in the catalog first and
only those that exist are read. The table proxy's ``get_sa_table`` is never
called on a Journal Table, because it creates the journal when it is missing.
A Table deleted between the catalog query and its read fails the run before
anything is written; run it again.

The cost is one catalog query plus one query per ``CHUNK`` journals, each
journal read with an index scan on its primary key (``_id`` comes from one
shared sequence, so the highest applied ``_id`` is the latest change). A
journal's ``_submitted`` is a ``timestamp without time zone`` written with the
OEDB's ``now()``. It is read back in the session's own time zone, which is
the one it was written in.

Prints what it would write unless ``--apply`` is given.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501

import time
from contextlib import contextmanager
from itertools import islice

from django.core.management.base import BaseCommand
from django.db.models import Case, DateTimeField, Max, Value, When
from sqlalchemy import text

from dataedit.models import BulkLoadEvent, Table
from oedb.connection import _get_engine

#: How many Journal Tables one OEDB query (and transaction) reads, and how
#: many Tables one UPDATE dates.
CHUNK = 200

#: The Journal Tables that exist, in the given meta schemas, with the three
#: columns this command reads.
EXISTING_JOURNALS = """
SELECT n.nspname, c.relname
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = ANY(:schemas)
  AND c.relkind IN ('r', 'p')
  AND (
    SELECT count(*) FROM pg_attribute a
    WHERE a.attrelid = c.oid
      AND NOT a.attisdropped
      AND a.attname IN ('_id', '_submitted', '_applied')
  ) = 3
"""

#: The latest applied change of one Journal Table, labelled with its index.
LATEST_APPLIED = (
    "(SELECT {index} AS journal,"
    " _submitted AT TIME ZONE current_setting('TimeZone') AS submitted"
    " FROM {schema}.{table}"
    " WHERE _applied AND _submitted IS NOT NULL"
    " ORDER BY _id DESC LIMIT 1)"
)


def _chunks(items, size):
    items = iter(items)
    while chunk := list(islice(items, size)):
        yield chunk


@contextmanager
def read_only(engine):
    """A connection in a READ ONLY transaction: the OEDB refuses any write."""
    with engine.connect() as connection, connection.begin():
        connection.execute(text("SET TRANSACTION READ ONLY"))
        yield connection


def journals_of(table):
    """``(schema, name)`` of the Table's three Journal Tables. The names come
    from the table proxy, which clips them as the journal's creator did; it
    creates nothing as long as ``get_sa_table`` is not called."""
    proxy = table.get_oedb_table_proxy()
    return [
        (journal.schema_name, journal.name)
        for journal in (proxy._insert_table, proxy._edit_table, proxy._delete_table)
    ]


def latest_journal_changes(tables):
    """``{pk: latest applied change}`` over the Edit Journals of ``tables``,
    plus how many Journal Tables were read and how many were skipped because
    more than one Table's journal name clips to them."""
    owners = {}
    for table in tables:
        for journal in journals_of(table):
            owners.setdefault(journal, []).append(table.pk)
    if not owners:
        return {}, 0, 0
    schemas = sorted({schema for schema, _ in owners})

    engine = _get_engine()
    with read_only(engine) as connection:
        existing = [
            (schema, name)
            for schema, name in connection.execute(
                text(EXISTING_JOURNALS), schemas=schemas
            )
            if (schema, name) in owners
        ]
    # Two Tables whose names clip to the same journal name write into one
    # journal, and nothing in it says which row is whose.
    readable = [journal for journal in existing if len(owners[journal]) == 1]
    shared = len(existing) - len(readable)

    latest, read = {}, 0
    quote = engine.dialect.identifier_preparer.quote_identifier
    for chunk in _chunks(readable, CHUNK):
        query = " UNION ALL ".join(
            LATEST_APPLIED.format(index=index, schema=quote(schema), table=quote(name))
            for index, (schema, name) in enumerate(chunk)
        )
        # A transaction of its own per chunk: a read locks the journal and its
        # index until the transaction ends, and a few thousand journals in one
        # would run out of the server's lock table.
        with read_only(engine) as connection:
            for index, submitted in connection.execute(text(query)):
                (pk,) = owners[chunk[index]]
                if pk not in latest or submitted > latest[pk]:
                    latest[pk] = submitted
        read += len(chunk)
    return latest, read, shared


def latest_bulk_loads():
    """``{table name: latest successful Bulk Load Event}``."""
    return dict(
        BulkLoadEvent.objects.filter(status=BulkLoadEvent.STATUS_SUCCESS)
        .values("table_name")
        .annotate(latest=Max("created"))
        .values_list("table_name", "latest")
    )


def fill(dates):
    """Write ``{pk: date}`` into ``data_modified`` where it is still NULL, and
    return how many Tables got a date."""
    filled = 0
    for chunk in _chunks(dates.items(), CHUNK):
        filled += Table.objects.filter(
            pk__in=[pk for pk, _ in chunk], data_modified__isnull=True
        ).update(
            data_modified=Case(
                *(When(pk=pk, then=Value(date)) for pk, date in chunk),
                output_field=DateTimeField(),
            )
        )
    return filled


class Command(BaseCommand):
    help = (
        "Fill Table.data_modified where it is NULL from the latest applied Edit "
        "Journal change and the latest successful Bulk Load Event. Prints what "
        "it would write unless --apply is given."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write the dates. Without it nothing is written.",
        )

    def handle(self, *args, **options):
        tables = list(
            Table.objects.only("pk", "name", "is_sandbox", "data_modified").order_by(
                "pk"
            )
        )
        started = time.perf_counter()
        journals, read, shared = latest_journal_changes(tables)
        seconds = time.perf_counter() - started
        bulk = latest_bulk_loads()

        sources = {"journal": 0, "bulk": 0, "both": 0, "neither": 0}
        dates, dated_already = {}, 0
        for table in tables:
            found = [
                date
                for date in (journals.get(table.pk), bulk.get(table.name))
                if date is not None
            ]
            if len(found) == 2:
                sources["both"] += 1
            elif not found:
                sources["neither"] += 1
            elif table.pk in journals:
                sources["journal"] += 1
            else:
                sources["bulk"] += 1
            if not found:
                continue
            if table.data_modified is None:
                dates[table.pk] = max(found)
            else:
                dated_already += 1

        self.stdout.write(
            f"Read {read:,} Edit Journal table(s) for {len(tables):,} table(s) "
            f"in {seconds:.2f} s."
        )
        if shared:
            self.stdout.write(
                f"  skipped {shared:,} journal(s) more than one table's name "
                "clips to"
            )
        self.stdout.write(f"  applied journal changes only: {sources['journal']:,}")
        self.stdout.write(f"  successful bulk loads only: {sources['bulk']:,}")
        self.stdout.write(f"  both: {sources['both']:,}")
        self.stdout.write(f"  neither, left unknown: {sources['neither']:,}")
        self.stdout.write(f"  already dated, left alone: {dated_already:,}")

        if not options["apply"]:
            self.stdout.write(f"Would date {len(dates):,} table(s).")
            self.stdout.write("Dry run, nothing was written. Re-run with --apply.")
            return

        filled = fill(dates)
        self.stdout.write(f"Dated {filled:,} table(s).")
        if filled < len(dates):
            self.stdout.write(
                f"  {len(dates) - filled:,} were stamped during the run, left alone"
            )
