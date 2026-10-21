"""The probes. Each returns wall time, query count, SQL time and bytes.

Query count is the headline number, not seconds: it is exact, deterministic,
machine-comparable across laptops, and it is the thing that regressed. The
two cost sites the map found are both visible in it (a 305-fold OR-combined
query, and 7 x N evaluations of `model.tags.all()`), and an
`assertNumQueries` bound is the regression test that would have caught them.
Seconds are recorded alongside because they are what the user feels.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from django.db import connection, reset_queries
from django.test.utils import CaptureQueriesContext


@dataclass
class Sample:
    probe: str
    seconds: float
    queries: int
    sql_seconds: float
    #: response body size - except for `tagloop`, which is not a request:
    #: there this is the number of ROWS the OR-combined queryset returned
    #: (undeduplicated, so it equals the factsheet->tag edge count).
    bytes: int
    status: int = 0

    def row(self) -> str:
        return "%-10s %9.3f s %7d q %9.3f s %11s" % (
            self.probe,
            self.seconds,
            self.queries,
            self.sql_seconds,
            "%.1f kB" % (self.bytes / 1024),
        )


def _measure(name: str, call) -> Sample:
    reset_queries()
    with CaptureQueriesContext(connection) as ctx:
        t0 = time.perf_counter()
        result = call()
        elapsed = time.perf_counter() - t0
    sql = sum(float(q.get("time", 0) or 0) for q in ctx.captured_queries)
    size, status = 0, 0
    if hasattr(result, "content"):
        size, status = len(result.content), result.status_code
    elif isinstance(result, int):
        size = result
    return Sample(name, elapsed, len(ctx.captured_queries), sql, size, status)


def probe_list(client, sheettype: str) -> Sample:
    """The page under investigation: /factsheets/models/."""
    url = "/factsheets/%ss/" % sheettype
    return _measure("list", lambda: client.get(url))


def probe_csv(client, sheettype: str) -> Sample:
    """The same rows, no template: the map's decisive contrast (0.336 s)."""
    url = "/factsheets/%ss/download/" % sheettype
    return _measure("csv", lambda: client.get(url))


def probe_detail(client, sheettype: str, pk: int) -> Sample:
    """One factsheet - the other cheap production probe (0.203 s)."""
    url = "/factsheets/%ss/%d/" % (sheettype, pk)
    return _measure("detail", lambda: client.get(url))


def probe_tagloop(model_cls, tag_cls) -> Sample:
    """Cost site 1 in isolation: `modelview/views.py:77-81`, verbatim.

    Isolating it is what lets WF-04 and WF-05 be judged separately - without
    this, a fix to either one is credited with the other's saving.
    """

    def run() -> int:
        tags = tag_cls.objects.none()
        for model in model_cls.objects.all():
            tags |= model.tags.all()
        return len(list(tags))

    return _measure("tagloop", run)
