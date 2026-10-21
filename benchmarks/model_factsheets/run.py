"""Command line for the model-factsheet list benchmark.

    # the default run: production's shape (305 models, 817 tags, measured
    # corruption rate), plus the small rungs that show the curve
    python -m benchmarks.model_factsheets.run

    # one rung only, and keep the seeded database to poke at it
    python -m benchmarks.model_factsheets.run --sweep 305 --keep-db

    # what the page costs once WF-03 has repaired the corrupted factsheets
    python -m benchmarks.model_factsheets.run --corrupt-fraction 0

    # frameworks instead of models
    python -m benchmarks.model_factsheets.run --sheettype framework --tags 817

This harness NEVER touches production and never touches a developer
database: it asks Django's own test runner for a throwaway test database,
seeds that, measures, and destroys it. All it needs is a reachable Postgres
(`docker run -d -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15`)
and the same environment variables `tox` passes.

Why it exists: one request to production's /factsheets/models/ takes ~400 s
and pins one of four mod_wsgi processes for nearly seven minutes, so a
before/after comparison there costs 25% of the platform for 40 minutes.
See the wayfinder ticket WF-01.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_RESULTS = Path("benchmarks/results/model_factsheets.csv")
DEFAULT_SWEEP = "25,50,100,200,305"


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m benchmarks.model_factsheets.run",
        description="Measure the Model/Framework Factsheet list page locally.",
    )
    p.add_argument(
        "--sweep",
        default=DEFAULT_SWEEP,
        help="comma-separated factsheet counts (default: %s). More "
        "than one rung is the point: the page grew 60 s -> 400 s, "
        "so a fix must be judged on the curve." % DEFAULT_SWEEP,
    )
    p.add_argument(
        "--tags",
        type=int,
        default=817,
        help="size of the tag vocabulary (production: 817)",
    )
    p.add_argument(
        "--corrupt-fraction",
        type=float,
        default=None,
        help="fraction of factsheets carrying a whole-tag-table "
        "snapshot (default: the measured 2/30). 0 models a "
        "corpus after WF-03's repair.",
    )
    p.add_argument("--sheettype", default="model", choices=("model", "framework"))
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--probes", default="csv,tagloop,list,detail")
    p.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    p.add_argument("--no-results", action="store_true")
    p.add_argument(
        "--keep-db",
        action="store_true",
        help="do not destroy the test database when finished",
    )
    return p.parse_args(argv)


def bootstrap():
    """Stand Django up and create a throwaway test database."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oeplatform.settings")
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import django

    django.setup()
    from django.conf import settings
    from django.test.runner import DiscoverRunner

    # DEBUG must be off (a debug-on run keeps every query in memory and
    # distorts the very numbers we are taking), which makes ALLOWED_HOSTS
    # bite - the test client speaks to "testserver".
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]
    runner = DiscoverRunner(verbosity=0, interactive=False)
    old_config = runner.setup_databases()
    return runner, old_config


def main(argv=None) -> int:
    args = parse_args(argv)
    runner, old_config = bootstrap()

    from django.test import Client

    from benchmarks.model_factsheets import bench
    from benchmarks.model_factsheets.profile import Corpus
    from benchmarks.model_factsheets.seed import seed
    from dataedit.models import Tag
    from modelview.helper import getClasses

    model_cls, _ = getClasses(args.sheettype)
    probes = [p.strip() for p in args.probes.split(",") if p.strip()]
    client = Client()
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []

    try:
        for rung in [int(n) for n in args.sweep.split(",")]:
            corpus = Corpus(
                models=rung, tags=args.tags, corrupt_fraction=args.corrupt_fraction
            )
            print(
                "\n=== %d factsheets, %d tags, corrupt=%s ==="
                % (
                    rung,
                    args.tags,
                    (
                        "measured"
                        if args.corrupt_fraction is None
                        else args.corrupt_fraction
                    ),
                )
            )
            written = seed(corpus, model_cls, Tag)
            first_pk = model_cls.objects.order_by("pk").values_list("pk", flat=True)[0]

            # One discarded request: the first one through Django pays for
            # template compilation and connection setup (~4 s here), which
            # would otherwise land on whichever probe happens to run first.
            client.get("/factsheets/%ss/download/" % args.sheettype)

            for attempt in range(args.repeats):
                for name in probes:
                    if name == "list":
                        s = bench.probe_list(client, args.sheettype)
                    elif name == "csv":
                        s = bench.probe_csv(client, args.sheettype)
                    elif name == "detail":
                        s = bench.probe_detail(client, args.sheettype, first_pk)
                    elif name == "tagloop":
                        s = bench.probe_tagloop(model_cls, Tag)
                    else:
                        raise SystemExit("unknown probe: %s" % name)
                    if s.status and s.status != 200:
                        raise SystemExit(
                            "probe %s returned HTTP %d - the measurement is "
                            "not valid" % (s.probe, s.status)
                        )
                    print("  " + s.row())
                    rows.append(
                        {
                            "run_utc": stamp,
                            "sheettype": args.sheettype,
                            "models": written["models"],
                            "tags": written["tags"],
                            "edges": written["edges"],
                            "attempt": attempt,
                            "probe": s.probe,
                            "seconds": round(s.seconds, 4),
                            "queries": s.queries,
                            "sql_seconds": round(s.sql_seconds, 4),
                            "bytes": s.bytes,
                            "status": s.status,
                        }
                    )
    finally:
        if args.keep_db:
            print("\ntest database kept (--keep-db)")
        else:
            runner.teardown_databases(old_config)

    if rows and not args.no_results:
        args.results.parent.mkdir(parents=True, exist_ok=True)
        exists = args.results.exists()
        with args.results.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            if not exists:
                w.writeheader()
            w.writerows(rows)
        print("\nappended %d rows to %s" % (len(rows), args.results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
