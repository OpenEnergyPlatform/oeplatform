"""What sharing with an Organization and removing it cost, for the ceilings (#2568).

    # the default: batches of 100 and 400 Tables, 6 KB and 60 KB of metadata
    python -m benchmarks.tables_tab.organization_cost

    python -m benchmarks.tables_tab.organization_cost --tables 1000 --metadata-kb 500

Spec #2551 owes these numbers: the dashboard shares a selection with one of
the user's Organizations at a role, or removes an Organization from it, in
one request, with no task queue, so the most Tables one request may name
(``CEILINGS["organization_share"]`` and ``CEILINGS["organization_remove"]``
in ``api/services/table_actions.py``) has to finish inside the host's
request timeout, with a stated safety factor.

Like ``dataset_cost.py`` this never touches production or a developer
database: it asks Django's test runner for a throwaway database. Who holds a
role lives in Django only, so no OEDB table is created.

For each metadata size and batch size it creates that many Tables shaped
like real ones (the metadata, an Admin grant of the user's own), an
Organization of the user's with ten members, and gives the Organization Data
editor on half of the Tables, so a share at Data maintainer both adds and
raises, then times, through the service the dashboard calls:

- ``check``: the preflight the dialog shows once an Organization and a role
  are chosen (``table_actions.preflight``), which runs the permission
  service's plan;
- ``share``: ``table_actions.execute`` sharing every Table at Data
  maintainer (an add or a change per Table, one log line each);
- ``remove``: ``table_actions.execute`` removing the Organization again.

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

DEFAULT_RESULTS = Path("benchmarks/results/tables_tab_organization.csv")


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m benchmarks.tables_tab.organization_cost",
        description=(
            "Measure what sharing Tables with an Organization and removing it cost."
        ),
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
    logging.getLogger("oeplatform.table_permissions").setLevel(logging.WARNING)

    from django.db import connection

    from api.services import table_actions
    from dataedit.models import Table
    from login.models import (
        ADMIN_PERM,
        DELETE_PERM,
        WRITE_PERM,
        GroupPermission,
        Membership,
        Organization,
        UserPermission,
        myuser,
    )

    def user(prefix):
        return myuser.objects.create(
            name=f"{prefix}_{uuid.uuid4().hex[:6]}",
            email=f"{prefix}_{uuid.uuid4().hex[:6]}@example.org",
            did_agree=True,
            is_mail_verified=True,
        )

    owner = user("bench_org")
    organization = Organization.objects.create(name=f"bench_{uuid.uuid4().hex[:6]}")
    Membership.objects.create(user=owner, group=organization)
    for _ in range(9):
        Membership.objects.create(user=user("bench_member"), group=organization)
    for action in table_actions.ORGANIZATION_ACTIONS:
        table_actions.CEILINGS[action] = None
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results = []

    def per_table(fn, n):
        connection.close()  # a fresh connection, like a request's
        start = time.perf_counter()
        fn()
        return round((time.perf_counter() - start) * 1000 / n, 2)

    share = table_actions.ORGANIZATION_SHARE
    remove = table_actions.ORGANIZATION_REMOVE
    try:
        for kb in [int(k) for k in args.metadata_kb.split(",")]:
            document = metadata(kb)
            for n in [int(t) for t in args.tables.split(",")]:
                names = [f"bench_org_{uuid.uuid4().hex[:10]}" for _ in range(n)]
                tables = Table.objects.bulk_create(
                    Table(name=name, oemetadata=document) for name in names
                )
                UserPermission.objects.bulk_create(
                    UserPermission(holder=owner, table=table, level=ADMIN_PERM)
                    for table in tables
                )
                GroupPermission.objects.bulk_create(
                    GroupPermission(holder=organization, table=table, level=WRITE_PERM)
                    for table in tables[::2]
                )
                params = {"organization": organization.pk, "level": DELETE_PERM}
                problem = table_actions.preflight(owner, share, names, params)
                assert len(problem.eligible) == n, problem.left_out

                check = per_table(
                    lambda: table_actions.preflight(owner, share, names, params),
                    n,
                )
                shared = per_table(
                    lambda: table_actions.execute(
                        owner, share, names, params, via="benchmark"
                    ),
                    n,
                )
                held = GroupPermission.objects.filter(
                    holder=organization, table__name__in=names, level=DELETE_PERM
                )
                assert held.count() == n
                removed = per_table(
                    lambda: table_actions.execute(
                        owner,
                        remove,
                        names,
                        {"organization": organization.pk},
                        via="benchmark",
                    ),
                    n,
                )
                assert not GroupPermission.objects.filter(
                    holder=organization, table__name__in=names
                ).exists()
                row = {
                    "run_utc": stamp,
                    "metadata_kb": kb,
                    "tables": n,
                    "check_per_table_ms": check,
                    "share_per_table_ms": shared,
                    "remove_per_table_ms": removed,
                }
                results.append(row)
                print(
                    "{metadata_kb:>4} KB x {tables:>4}: per Table check "
                    "{check_per_table_ms} ms, share {share_per_table_ms} ms, "
                    "remove {remove_per_table_ms} ms".format(**row)
                )
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
