"""What publishing and unpublishing one Table cost, to set their ceilings (#2564).

    # the default: batches of 100 and 400 Tables, 6 KB and 60 KB of metadata
    python -m benchmarks.tables_tab.publish_cost

    python -m benchmarks.tables_tab.publish_cost --tables 200 --metadata-kb 500

Spec #2551 owes these numbers: the dashboard publishes and unpublishes a
selection in one request, with no task queue, so the most Tables one request
may name (``CEILINGS["publish"]`` and ``CEILINGS["unpublish"]`` in
``api/services/table_actions.py``) has to finish inside the host's request
timeout, with a stated safety factor.

Like ``delete_cost.py`` this never touches production or a developer
database: it asks Django's test runner for a throwaway database. Publishing
moves nothing in the OEDB any more, so no OEDB table is created.

For each metadata size and batch size it creates that many draft Tables
shaped like a real one (the metadata, an open data license, a Table admin
grant, a finished peer review, which publishing rewrites), then times the
three requests a bulk publish and a bulk unpublish make, through the service
the dashboard calls:

- ``check``: the preflight the dialog shows (``table_actions.preflight``),
  once with the stored Publish gate verdict set (the common case) and once
  with none, which runs the gate live for every Table;
- ``publish``: ``table_actions.execute`` with a Topic and a 6-month embargo,
  the heaviest publish (it writes an embargo too);
- ``unpublish``: ``table_actions.execute`` on the same Tables.

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

from benchmarks.tables_tab.run import bootstrap

DEFAULT_RESULTS = Path("benchmarks/results/tables_tab_publish.csv")
LICENSE = {
    "name": "CC-BY-4.0",
    "title": "Creative Commons Attribution 4.0 International",
}


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m benchmarks.tables_tab.publish_cost",
        description="Measure what publishing and unpublishing one Table cost.",
    )
    p.add_argument("--tables", default="100,400")
    p.add_argument("--metadata-kb", default="6,60")
    p.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    p.add_argument("--no-results", action="store_true")
    return p.parse_args(argv)


def metadata(kb: int) -> dict:
    """An oemetadata document of about ``kb`` KB with an open license."""
    return {
        "metaMetadata": {"metadataVersion": "OEMetadata-2.0.4"},
        "name": "bench",
        "title": "Bench",
        "resources": [
            {
                "name": "bench",
                "description": "y" * (kb * 1024),
                "licenses": [LICENSE],
            }
        ],
    }


def main(argv=None) -> int:
    args = parse_args(argv)
    runner, old_config = bootstrap()
    # one line per Table is the service's record, not this measurement's
    logging.getLogger("oeplatform.table_actions").setLevel(logging.WARNING)

    from django.db import connection

    from api.services import table_actions
    from dataedit.models import PeerReview, Table, Topic
    from login.models import ADMIN_PERM, UserPermission, myuser

    owner = myuser.objects.create(
        name=f"bench_publish_{uuid.uuid4().hex[:6]}",
        email=f"bench_{uuid.uuid4().hex[:6]}@example.org",
        did_agree=True,
        is_mail_verified=True,
    )
    topic = Topic.objects.exclude(name="draft").first()
    if topic is None:
        topic = Topic.objects.create(name="bench_topic")
    for action in (table_actions.PUBLISH, table_actions.UNPUBLISH):
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
                names = [f"bench_pub_{uuid.uuid4().hex[:10]}" for _ in range(n)]
                tables = Table.objects.bulk_create(
                    Table(name=name, oemetadata=document, publishable=True)
                    for name in names
                )
                UserPermission.objects.bulk_create(
                    UserPermission(holder=owner, table=table, level=ADMIN_PERM)
                    for table in tables
                )
                PeerReview.objects.bulk_create(
                    PeerReview(table=name, is_finished=True, review={"badge": "Gold"})
                    for name in names
                )
                problem = table_actions.preflight(owner, "publish", names)
                assert len(problem.eligible) == n, problem.left_out

                stored = per_table(
                    lambda: table_actions.preflight(owner, "publish", names), n
                )
                Table.objects.filter(name__in=names).update(publishable=None)
                live = per_table(
                    lambda: table_actions.preflight(owner, "publish", names), n
                )
                Table.objects.filter(name__in=names).update(publishable=True)
                publish = per_table(
                    lambda: table_actions.execute(
                        owner,
                        "publish",
                        names,
                        {"topic": topic.name, "embargo": "6_months"},
                        via="benchmark",
                    ),
                    n,
                )
                unpublish = per_table(
                    lambda: table_actions.execute(
                        owner, "unpublish", names, via="benchmark"
                    ),
                    n,
                )
                row = {
                    "run_utc": stamp,
                    "metadata_kb": kb,
                    "tables": n,
                    "check_stored_per_table_ms": stored,
                    "check_live_per_table_ms": live,
                    "publish_per_table_ms": publish,
                    "unpublish_per_table_ms": unpublish,
                }
                results.append(row)
                print(
                    "{metadata_kb:>4} KB x {tables:>4}: per Table check "
                    "{check_stored_per_table_ms} ms (stored) / "
                    "{check_live_per_table_ms} ms (live), publish "
                    "{publish_per_table_ms} ms, unpublish "
                    "{unpublish_per_table_ms} ms".format(**row)
                )
                Table.objects.filter(name__in=names).delete()
                PeerReview.objects.filter(table__in=names).delete()
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
