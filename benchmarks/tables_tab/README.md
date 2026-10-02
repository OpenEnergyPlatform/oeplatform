<!--
SPDX-FileCopyrightText: none
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Profile dashboard tables tab: row cost and column widths

Three measurements spec #2551 owes for the tables tab, none of which a test can
take:

- **`run.py`**: what one row of the list costs the server, against the old
  profile cards' 6-10 ms each;
- **`widths.mjs`**: how wide the list must be for each set of columns, which
  sets the container-query thresholds in `login/static/login/tables_tab.css`.
  happy-dom has no layout, so this runs in a real browser.
- **`delete_cost.py`**: what deleting one Table costs (#2562), which sets the
  delete ceiling `CEILINGS["delete"]` in `api/services/table_actions.py`.
- **`publish_cost.py`**: what publishing and unpublishing one Table cost
  (#2564), which sets `CEILINGS["publish"]` and `CEILINGS["unpublish"]`.

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

## Delete cost

Same throwaway database as the row cost; the OEDB tables go into the sandbox
schema under names nobody else uses, and the measurement drops them itself.

```bash
python -m benchmarks.tables_tab.delete_cost
python -m benchmarks.tables_tab.delete_cost --rows 10000000 --tables 2
```

Each size creates `--tables` Tables filled with that many rows (an OEDB table
with a primary key and three data columns, its three meta tables, 6 KB of
metadata, a grant, a Topic and a Dataset membership) and deletes them all in one
`table_actions.execute` call, the dashboard's path. Results append to
`benchmarks/results/tables_tab_delete.csv`. Keep the 1M- and 10M-row batches
small: filling them is what takes the time.

Measured 2026-10-02, local Postgres 14 (`shared_buffers` 128 MB), three rounds:

| rows per Table      | per Table, total | of which the drop | slowest single drop |
| ------------------- | ---------------- | ----------------- | ------------------- |
| 0 (16 KB)           | 17-18 ms         | 9-10 ms           | 13 ms               |
| 100,000 (8 MB)      | 17-18 ms         | 10-11 ms          | 14 ms               |
| 1,000,000 (83 MB)   | 33-38 ms         | 22-24 ms          | 1,020 ms (once)     |
| 10,000,000 (0.8 GB) | 0.64 s           | 0.62 s            | 1,126 ms            |

The drop is most of it and grows with the table's size; a single drop
occasionally takes about a second (one 1M-row drop in three rounds). The
production timeout is `Timeout 300` / `socket-timeout=300` (read on the host
2026-10-02). At a worst case of 1.2 s per Table, 50 Tables take 60 s: the
ceiling is 50, a safety factor of 5, which covers production's OEDB sitting on
another host. The reasoning is beside the constant.

## Publish and unpublish cost

Same throwaway database; publishing moves nothing in the OEDB, so no OEDB table
is created.

```bash
python -m benchmarks.tables_tab.publish_cost
python -m benchmarks.tables_tab.publish_cost --tables 100,400,1000 --metadata-kb 6,60,500
```

For each metadata size and batch size it creates draft Tables with an open
license, a Table admin grant and a finished peer review (which publishing
rewrites), then times the preflight (stored Publish gate verdict, and none,
which runs the gate live), a publish with a 6-month embargo and an unpublish,
through `table_actions`. Results append to
`benchmarks/results/tables_tab_publish.csv`.

Measured 2026-10-02/03, local Postgres 14, batches of 100, 400 and 1,000, three
rounds, per Table:

| metadata per Table | preflight  | publish  | unpublish  |
| ------------------ | ---------- | -------- | ---------- |
| 6 KB               | 0.1-0.3 ms | 6-7.5 ms | 1.6-2.1 ms |
| 60 KB              | 0.4-0.5 ms | 7-9 ms   | 2.8-4.2 ms |
| 500 KB             | 3.0-5.0 ms | 20-34 ms | 16-21 ms   |

The preflight costs the same with the stored verdict as with the gate run live:
decoding the metadata is what it pays for. Both writes save the whole row, which
is why they grow with the metadata. At the worst 34 ms, 1,000 Tables take 34 s
against production's 300 s timeout: the ceiling is 1,000 for both, a safety
factor of about 9. The reasoning is beside the constant.
