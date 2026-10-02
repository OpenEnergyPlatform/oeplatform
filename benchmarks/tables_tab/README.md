<!--
SPDX-FileCopyrightText: none
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Profile dashboard tables tab: row cost and column widths

Two measurements spec #2551 owes for the tables tab (#2555), neither of which a
test can take:

- **`run.py`**: what one row of the list costs the server, against the old
  profile cards' 6-10 ms each;
- **`widths.mjs`**: how wide the list must be for each set of columns, which
  sets the container-query thresholds in `login/static/login/tables_tab.css`.
  happy-dom has no layout, so this runs in a real browser.

Both use accounts shaped like production (`seed.py`, a port of the WF-06
prototype's generator, sized from WF-01's census): `p90` (130 Tables), `max`
(2,068, mixed) and `maxreal` (2,068 as measured: all draft, all direct).

## Row cost

Like `benchmarks/model_factsheets`, this asks Django's test runner for a
throwaway database, seeds it, measures and drops it; it never opens a developer
database or production.

```bash
python -m benchmarks.tables_tab.run
python -m benchmarks.tables_tab.run --metadata-kb 6,60,500
```

Results append to `benchmarks/results/tables_tab.csv`. `--metadata-kb` matters:
the page query decodes each row's whole oemetadata for the live Publish gate,
and real documents range from a few KB to several hundred.

Measured 2026-10-02 (medians of 7, first 6 pages, 7 queries per request at every
size):

| metadata per Table | per row (marginal) | building the rows | rendering the row |
| ------------------ | ------------------ | ----------------- | ----------------- |
| 6 KB               | 0.8-1.2 ms         | 0.6-1.0 ms        | 0.34-0.47 ms      |
| 60 KB              | 1.4-2.2 ms         | 1.3-2.1 ms        | 0.34-0.47 ms      |
| 500 KB             | 5.8-7.5 ms         | 4.9-8.1 ms        | 0.34-0.47 ms      |

The template is constant and well under the cards' 6-10 ms; what grows is the
metadata the gate decodes. A short final page reads high per row because the
request's fixed cost (8-15 ms) is spread over fewer rows.

## Column widths

Needs a dev server on a database holding the seeded accounts and puppeteer-core
with a Chrome; the header of `widths.mjs` says how to run it. Seed the accounts
into that database with:

```python
from django.test import Client
from benchmarks.tables_tab.seed import seed_account

used = set()
for key in ("p90", "max", "maxreal"):
    owner = seed_account(key, used=used)
    client = Client()
    client.force_login(owner)
    print(key, owner.pk, client.cookies["sessionid"].value)
```

The numbers it produced, and the thresholds taken from them, are written beside
the container queries in `tables_tab.css`. A slice that adds a column re-runs it
and moves the thresholds; with `STAND_INS=1` it also measures the complete row,
standing in only for the columns that are still missing.
