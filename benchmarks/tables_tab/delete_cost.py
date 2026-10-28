"""What deleting one Table costs, to set the delete ceiling (#2562).

    # the default: 10 Tables each at 0, 100,000 and 1,000,000 rows
    python -m benchmarks.tables_tab.delete_cost

    python -m benchmarks.tables_tab.delete_cost --rows 0,1000000 --tables 5

Spec #2551 owes this number: the dashboard deletes in one request, with no
task queue, so the most Tables one request may name (``CEILINGS["delete"]``
in ``api/services/table_actions.py``) has to finish inside the host's
request timeout, with a stated safety factor.

Like ``run.py`` this never touches production or a developer database: it
asks Django's test runner for a throwaway database. The OEDB tables go into
the sandbox schema of the configured OEDB, on names nobody else uses, and are
dropped by the measurement itself (and again on the way out, whatever
happened).

For each row count it creates ``--tables`` Tables shaped like a real one (an
OEDB table with a primary key and three data columns, filled with that many
rows, plus its three meta tables; on the Django side 6 KB of metadata, a
Table admin grant, a Topic and a Dataset membership), then deletes them all
in one ``table_actions.execute`` call, the path the dashboard takes, and
reports per Table:

- ``total``: the whole call divided by the Tables in it;
- ``drop``: the OEDB drops alone (four ``DROP TABLE`` each), timed one by one;
- ``django``: the rest (the re-check under a row lock, the cascade delete,
  the log lines).
"""

from __future__ import annotations

import argparse
import csv
import statistics
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from benchmarks.tables_tab.run import bootstrap

DEFAULT_RESULTS = Path("benchmarks/results/tables_tab_delete.csv")
METADATA_KB = 6


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m benchmarks.tables_tab.delete_cost",
        description="Measure what deleting one Table costs, locally.",
    )
    p.add_argument("--rows", default="0,100000,1000000")
    p.add_argument("--tables", type=int, default=10)
    p.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    p.add_argument("--no-results", action="store_true")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    runner, old_config = bootstrap()

    from django.db import connection
    from sqlalchemy import text

    from api.services import table_actions
    from dataedit.models import Dataset, Table, Topic
    from login.models import myuser
    from oedb.connection import _get_engine

    engine = _get_engine()
    owner = myuser.objects.create(
        name=f"bench_delete_{uuid.uuid4().hex[:6]}",
        email=f"bench_{uuid.uuid4().hex[:6]}@example.org",
        did_agree=True,
        is_mail_verified=True,
    )
    dataset = Dataset.objects.create(name="bench_delete", creator=owner)
    topic = Topic.objects.exclude(name="draft").first()
    metadata = {"title": "x", "description": "y" * (METADATA_KB * 1024)}
    columns = [
        {"name": "id", "data_type": "bigserial", "primary_key": True},
        {"name": "region", "data_type": "text"},
        {"name": "year", "data_type": "integer"},
        {"name": "value", "data_type": "float"},
    ]
    schema = Table.get_oedb_schema(is_sandbox=True)
    created = []
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results = []
    try:
        for rows in [int(r) for r in args.rows.split(",")]:
            names = []
            for _ in range(args.tables):
                name = f"bench_del_{uuid.uuid4().hex[:10]}"
                table = Table.create_with_oedb_table(
                    name=name,
                    is_sandbox=True,
                    user=owner,
                    column_definitions=columns,
                    constraints_definitions=[],
                )
                created.append(table)
                names.append(name)
                Table.objects.filter(pk=table.pk).update(oemetadata=metadata)
                table.topics.add(topic)
                dataset.tables.add(table)
                if rows:
                    with engine.begin() as conn:
                        conn.execute(
                            text(
                                f'INSERT INTO "{schema}"."{name}" '
                                "(region, year, value) "
                                "SELECT 'region_' || (g % 400), 2000 + g % 50, "
                                "random() FROM generate_series(1, :n) g"
                            ),
                            n=rows,
                        )
            with engine.connect() as conn:
                size = conn.execute(
                    text("SELECT pg_total_relation_size(:t)"),
                    t=f'"{schema}"."{names[0]}"',
                ).scalar()

            drops = []
            real = Table.drop_oedb_table

            def timed(instance):
                start = time.perf_counter()
                real(instance)
                drops.append((time.perf_counter() - start) * 1000)

            Table.drop_oedb_table = timed
            table_actions.CEILINGS[table_actions.DELETE] = None
            connection.close()  # a fresh connection, like a request's
            start = time.perf_counter()
            try:
                table_actions.execute(
                    owner,
                    table_actions.DELETE,
                    names,
                    {"confirm": str(len(names))},
                    via="benchmark",
                )
            finally:
                Table.drop_oedb_table = real
            total_ms = (time.perf_counter() - start) * 1000
            row = {
                "run_utc": stamp,
                "rows": rows,
                "bytes_per_table": size,
                "tables": len(names),
                "total_per_table_ms": round(total_ms / len(names), 2),
                "drop_per_table_ms": round(sum(drops) / len(names), 2),
                "drop_median_ms": round(statistics.median(drops), 2),
                "drop_max_ms": round(max(drops), 2),
                "django_per_table_ms": round((total_ms - sum(drops)) / len(names), 2),
            }
            results.append(row)
            print(
                "{rows:>9,} rows ({bytes_per_table:,} B): per Table "
                "{total_per_table_ms} ms = drop {drop_per_table_ms} (median "
                "{drop_median_ms}, max {drop_max_ms}) + django "
                "{django_per_table_ms}".format(**row)
            )
    finally:
        for table in created:
            table.drop_oedb_table()
        runner.teardown_databases(old_config)

    if results and not args.no_results:
        args.results.parent.mkdir(parents=True, exist_ok=True)
        exists = args.results.exists()
        with args.results.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(results[0]))
            if not exists:
                writer.writeheader()
            writer.writerows(results)
        print(f"\nappended {len(results)} rows to {args.results}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
