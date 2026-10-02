"""What one row of the profile dashboard's tables tab costs the server.

    # the default: the 130 and the two 2,068 accounts, 6 KB of metadata
    python -m benchmarks.tables_tab.run

    # does the cost follow the metadata size? (the gate decodes it per row)
    python -m benchmarks.tables_tab.run --metadata-kb 6,100

Spec #2551 owes this number for #2555: the old profile cards cost 6-10 ms
each (WF-01, rendered in-process on production); a row of the new list must
not cost more than about 10 ms, or the slice records why and what it
trimmed.

Like ``benchmarks.model_factsheets`` this never touches production or a
developer database: it asks Django's test runner for a throwaway database,
seeds accounts shaped like production (``seed.py``), measures, and drops it.
All it needs is a reachable Postgres and the variables ``tox`` passes.

For each account it takes, as medians of ``--repeats`` runs:

- ``request``: one htmx request for a page of the list, through the test
  client and the real view, middleware included;
- ``empty``: the same request filtered to no rows. Everything a request
  costs whatever the page holds (session, facet counts, the bar's state);
- ``per row``: (request - empty) / rows, the marginal cost of a row;
- ``build`` and ``render``: the same page split into building the rows
  (``Listing.page`` with ``table_rows``, its queries included) and rendering
  the region template, each per row. ``render`` is the figure to hold
  against the old cards' 6-10 ms, which were template renders too.

Query counts are recorded next to the seconds; they are exact and the same
on every machine, and the tab's tests pin them (7 per request).
"""

from __future__ import annotations

import argparse
import csv
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_RESULTS = Path("benchmarks/results/tables_tab.csv")
NOTHING = "zz-matches-no-table-zz"


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m benchmarks.tables_tab.run",
        description="Measure the server cost of one tables-tab row locally.",
    )
    p.add_argument("--accounts", default="p90,max,maxreal")
    p.add_argument(
        "--metadata-kb",
        default="6",
        help="comma-separated oemetadata sizes per Table, one seeding each "
        "(default 6; real documents range from a few KB to several hundred)",
    )
    p.add_argument("--pages", type=int, default=6, help="first n pages of each")
    p.add_argument("--repeats", type=int, default=7)
    p.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    p.add_argument("--no-results", action="store_true")
    p.add_argument("--keep-db", action="store_true")
    return p.parse_args(argv)


def bootstrap():
    """Stand Django up and create a throwaway test database."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oeplatform.settings")
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import django

    django.setup()
    from django.conf import settings
    from django.test.runner import DiscoverRunner

    # DEBUG off, or every query is kept in memory and distorts the numbers
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]
    runner = DiscoverRunner(verbosity=0, interactive=False)
    return runner, runner.setup_databases()


def median_ms(fn, repeats):
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000)
    return statistics.median(samples)


def main(argv=None) -> int:
    args = parse_args(argv)
    runner, old_config = bootstrap()

    from django.db import connection
    from django.template.loader import render_to_string
    from django.test import Client, RequestFactory
    from django.urls import reverse

    from benchmarks.tables_tab.seed import seed_account
    from login.tables_tab import accessible_tables, table_rows, tables_listing

    htmx = {"HTTP_HX_REQUEST": "true"}
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results, used = [], set()
    try:
        for kb in [float(k) for k in args.metadata_kb.split(",")]:
            for key in [a.strip() for a in args.accounts.split(",") if a.strip()]:
                label = f"{key}_{kb:g}kb"
                owner = seed_account(key, metadata_kb=kb, used=used, label=label)
                n = accessible_tables(owner).count()
                path = reverse("login:tables", kwargs={"user_id": owner.pk})
                client = Client()
                client.force_login(owner)
                # one discarded request: template compilation, the Site cache
                client.get(path, **htmx)
                print(f"\n=== {key}: {n:,} tables, {kb:g} KB metadata each ===")

                empty_ms = median_ms(
                    lambda: client.get(path, {"search": NOTHING}, **htmx),
                    args.repeats,
                )
                pages = min(args.pages, -(-n // 25))
                for number in range(1, pages + 1):
                    query = {"page": str(number)} if number > 1 else {}
                    queries = []
                    with connection.execute_wrapper(
                        lambda execute, sql, *rest: queries.append(sql)
                        or execute(sql, *rest)
                    ):
                        response = client.get(path, query, **htmx)
                    assert response.status_code == 200, response.status_code
                    request_ms = median_ms(
                        lambda: client.get(path, query, **htmx), args.repeats
                    )

                    request = RequestFactory().get(path, query, **htmx)
                    request.user = owner
                    listing = tables_listing(owner)

                    def build():
                        return listing.page(
                            accessible_tables(owner),
                            request.GET,
                            path,
                            rows=table_rows(owner),
                        )

                    build_ms = median_ms(build, args.repeats)
                    page = build()
                    rows = len(page.rows)
                    context = {"profile_user": owner, "page": page}
                    render_ms = median_ms(
                        lambda: render_to_string(
                            "login/partials/tables_region.html", context, request
                        ),
                        args.repeats,
                    )
                    row = {
                        "run_utc": stamp,
                        "account": key,
                        "tables": n,
                        "metadata_kb": kb,
                        "page": number,
                        "rows": rows,
                        "queries": len(queries),
                        "bytes": len(response.content),
                        "request_ms": round(request_ms, 2),
                        "empty_ms": round(empty_ms, 2),
                        "per_row_ms": round((request_ms - empty_ms) / rows, 3),
                        "build_per_row_ms": round(build_ms / rows, 3),
                        "render_per_row_ms": round(render_ms / rows, 3),
                    }
                    results.append(row)
                    print(
                        "  page {page}: {rows} rows, {queries} queries, "
                        "{bytes:,} B | request {request_ms} ms, empty {empty_ms} "
                        "ms | per row {per_row_ms} ms (build "
                        "{build_per_row_ms}, render {render_per_row_ms})".format(**row)
                    )
    finally:
        if args.keep_db:
            print("\ntest database kept (--keep-db)")
        else:
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
