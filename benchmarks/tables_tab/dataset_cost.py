"""What adding a Table to a Dataset and removing it cost, to set their ceilings (#2565).

    # the default: batches of 100 and 400 Tables, 6 KB and 60 KB of metadata
    python -m benchmarks.tables_tab.dataset_cost

    python -m benchmarks.tables_tab.dataset_cost --tables 1000 --metadata-kb 500

Spec #2551 owes these numbers: the dashboard adds a selection to one of the
user's own Datasets, or removes it, in one request, with no task queue, so
the most Tables one request may name (``CEILINGS["dataset_add"]`` and
``CEILINGS["dataset_remove"]`` in ``api/services/table_actions.py``) has to
finish inside the host's request timeout, with a stated safety factor.

Like ``publish_cost.py`` this never touches production or a developer
database: it asks Django's test runner for a throwaway database. Dataset
membership lives in Django only, so no OEDB table is created.

For each metadata size and batch size it creates that many Tables shaped
like real ones (the metadata, a Data editor grant, two Topics each, which
adding seeds into the Dataset), half of them drafts (the curation rule reads
the grant for those) and half published, and one Dataset of the user's own,
then times what a bulk add and a bulk remove do, through the service the
dashboard calls:

- ``check``: the preflight the dialog shows once a Dataset is chosen
  (``table_actions.preflight`` with ``dataset``), which also runs the
  curation rule and the membership split;
- ``add``: ``table_actions.execute`` adding every Table;
- ``remove``: ``table_actions.execute`` removing them again.

Each is reported per Table: the whole call divided by the Tables in it.
"""

from __future__ import annotations

import argparse
import csv
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from benchmarks.tables_tab.publish_cost import metadata
from benchmarks.tables_tab.run import bootstrap

DEFAULT_RESULTS = Path("benchmarks/results/tables_tab_dataset.csv")


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m benchmarks.tables_tab.dataset_cost",
        description="Measure what adding a Table to a Dataset and removing it cost.",
    )
    p.add_argument("--tables", default="100,400")
    p.add_argument("--metadata-kb", default="6,60")
    p.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    p.add_argument("--no-results", action="store_true")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    runner, old_config = bootstrap()
    # one line per Table is the service's record, not this measurement's
    logging.getLogger("oeplatform.table_actions").setLevel(logging.WARNING)

    from django.db import connection

    from api.services import table_actions
    from dataedit.models import Dataset, Table, Topic
    from login.models import WRITE_PERM, UserPermission, myuser

    owner = myuser.objects.create(
        name=f"bench_dataset_{uuid.uuid4().hex[:6]}",
        email=f"bench_{uuid.uuid4().hex[:6]}@example.org",
        did_agree=True,
        is_mail_verified=True,
    )
    topics = [
        Topic.objects.get_or_create(name=name)[0]
        for name in ("bench_topic_a", "bench_topic_b")
    ]
    for action in table_actions.DATASET_ACTIONS:
        table_actions.CEILINGS[action] = None
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results = []

    def per_table(fn, n):
        connection.close()  # a fresh connection, like a request's
        start = time.perf_counter()
        fn()
        return round((time.perf_counter() - start) * 1000 / n, 2)

    try:
        for kb in [int(k) for k in args.metadata_kb.split(",")]:
            document = metadata(kb)
            for n in [int(t) for t in args.tables.split(",")]:
                names = [f"bench_ds_{uuid.uuid4().hex[:10]}" for _ in range(n)]
                tables = Table.objects.bulk_create(
                    Table(name=name, oemetadata=document, is_publish=i % 2 == 0)
                    for i, name in enumerate(names)
                )
                UserPermission.objects.bulk_create(
                    UserPermission(holder=owner, table=table, level=WRITE_PERM)
                    for table in tables
                )
                for topic in topics:
                    topic.tables.add(*tables)
                dataset = Dataset.objects.create(
                    name=f"bench_ds_{uuid.uuid4().hex[:8]}",
                    metadata={"title": "Bench"},
                    creator=owner,
                )
                params = {"dataset": dataset.name}
                problem = table_actions.preflight(owner, "dataset_add", names, params)
                assert len(problem.eligible) == n, problem.left_out

                check = per_table(
                    lambda: table_actions.preflight(
                        owner, "dataset_add", names, params
                    ),
                    n,
                )
                add = per_table(
                    lambda: table_actions.execute(
                        owner, "dataset_add", names, params, via="benchmark"
                    ),
                    n,
                )
                assert dataset.tables.count() == n
                remove = per_table(
                    lambda: table_actions.execute(
                        owner, "dataset_remove", names, params, via="benchmark"
                    ),
                    n,
                )
                assert dataset.tables.count() == 0
                row = {
                    "run_utc": stamp,
                    "metadata_kb": kb,
                    "tables": n,
                    "check_per_table_ms": check,
                    "add_per_table_ms": add,
                    "remove_per_table_ms": remove,
                }
                results.append(row)
                print(
                    "{metadata_kb:>4} KB x {tables:>4}: per Table check "
                    "{check_per_table_ms} ms, add {add_per_table_ms} ms, "
                    "remove {remove_per_table_ms} ms".format(**row)
                )
                dataset.delete()
                Table.objects.filter(name__in=names).delete()
    finally:
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
