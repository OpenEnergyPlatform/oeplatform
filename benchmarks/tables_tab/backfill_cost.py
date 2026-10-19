"""What the ``backfill_data_modified`` command costs (#2558).

    # the default: 300 Tables, 1,000 rows in each journal that exists
    python -m benchmarks.tables_tab.backfill_cost

    python -m benchmarks.tables_tab.backfill_cost --tables 2000 --rows 10000

The command runs once on deploy, where the OEDB is reachable, and reads one
catalog query plus one ``UNION ALL`` query per ``CHUNK`` Journal Tables. This
says how long that is for an account-sized set of Tables.

Like ``run.py`` this never touches production or a developer database: it
asks Django's test runner for a throwaway database. The Journal Tables go
into the sandbox meta schema of the configured OEDB, on names nobody else
uses, and are dropped on the way out, whatever happened.

The Tables are mixed like a real account: half carry all three journals, a
quarter only the insert journal, a quarter none; every fifth has successful
Bulk Load Events. A journal holds ``--rows`` changes, nine in ten applied.
"""

from __future__ import annotations

import argparse
import statistics
import time
import uuid
from io import StringIO

from benchmarks.tables_tab.run import bootstrap


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m benchmarks.tables_tab.backfill_cost",
        description="Measure what backfilling data_modified costs, locally.",
    )
    p.add_argument("--tables", type=int, default=300)
    p.add_argument("--rows", type=int, default=1000)
    p.add_argument("--repeats", type=int, default=3)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    runner, old_config = bootstrap()

    from django.core.management import call_command
    from sqlalchemy import text

    from dataedit.models import BulkLoadEvent, Table
    from oedb.connection import _get_engine

    engine = _get_engine()
    meta_schema = "_" + Table.get_oedb_schema(is_sandbox=True)
    prefix = f"bench_bf_{uuid.uuid4().hex[:6]}"
    journals = []
    try:
        tables = Table.objects.bulk_create(
            [Table(name=f"{prefix}_{i}", is_sandbox=True) for i in range(args.tables)]
        )
        events = []
        for i, table in enumerate(tables):
            # One transaction per Table: thousands of CREATE TABLEs in one
            # run out of the server's lock table.
            with engine.begin() as conn:
                actions = (
                    ("insert", "edit", "delete")
                    if i % 4 < 2
                    else ("insert",) if i % 4 == 2 else ()
                )
                for action in actions:
                    journal = f'"{meta_schema}"."_{table.name}_{action}"'
                    journals.append(journal)
                    conn.execute(
                        text(
                            f"CREATE TABLE {journal} (PRIMARY KEY (_id)) "
                            "INHERITS (public._edit_base)"
                        )
                    )
                    conn.execute(
                        text(
                            f"INSERT INTO {journal} (_user, _type, _applied) "
                            "SELECT 'bench', :action, g % 10 <> 0 "
                            "FROM generate_series(1, :n) g"
                        ),
                        action=action,
                        n=args.rows,
                    )
                if i % 5 == 0:
                    events += [
                        BulkLoadEvent(
                            table_name=table.name,
                            status=BulkLoadEvent.STATUS_SUCCESS,
                        )
                        for _ in range(3)
                    ]
        BulkLoadEvent.objects.bulk_create(events)

        def run(*options):
            out = StringIO()
            start = time.perf_counter()
            call_command("backfill_data_modified", *options, stdout=out)
            return (time.perf_counter() - start) * 1000, out.getvalue()

        dry = [run()[0] for _ in range(args.repeats)]
        applied_ms, output = run("--apply")
        print(output.rstrip())
        print(
            f"\n{args.tables:,} Tables, {len(journals):,} journals of "
            f"{args.rows:,} rows: dry run {statistics.median(dry):.0f} ms "
            f"(median of {args.repeats}), --apply {applied_ms:.0f} ms, "
            f"{statistics.median(dry) / args.tables:.2f} ms per Table"
        )
    finally:
        for journal in journals:
            with engine.begin() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {journal}"))
        runner.teardown_databases(old_config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
