<!--
SPDX-FileCopyrightText: none
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Model Factsheet list-page benchmark

`/factsheets/models/` takes about **400 seconds** on production. This harness
produces before/after numbers for it **without touching production**.

It exists because measuring on production is prohibitively expensive: one
request pins one of the four `mod_wsgi` processes for nearly seven minutes, so a
naive "three runs before, three runs after" is forty minutes at 75% capacity.
The harness seeds a synthetic corpus with production's _shape_ into a Django
test database and measures that instead.

## Running it

Any reachable Postgres will do - the harness creates and destroys its own test
database and never opens the developer database. The project's own dev Postgres
is the easiest one, and no other service from that file is needed:

```bash
docker compose -f docker/docker-compose.dev.yaml up -d postgres

export OEP_DJANGO_HOST=localhost OEP_DB_PW=postgres OEP_DJANGO_USER=postgres
export LOCAL_DB_HOST=localhost LOCAL_DB_PASSWORD=postgres

python -m benchmarks.model_factsheets.run
```

Results append to `benchmarks/results/model_factsheets.csv`.

| Flag                               | Why you would use it                                                                                                                                       |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--sweep 25,50,100,200,305`        | the rungs. **More than one is the point** - the page went 60 s -> 400 s while the data grew modestly, so a fix is judged on the _curve_, not on one number |
| `--corrupt-fraction 0`             | a corpus with no #2385 damage, i.e. what the platform looks like after WF-03's repair                                                                      |
| `--tags 817`                       | size of the shared tag vocabulary                                                                                                                          |
| `--sheettype framework`            | the other list page, same view and template                                                                                                                |
| `--probes csv,tagloop,list,detail` | which probes to take                                                                                                                                       |
| `--keep-db`                        | leave the seeded test database behind to poke at                                                                                                           |

## What is measured, and why query count is the headline

| Probe     | What it isolates                                                                     |
| --------- | ------------------------------------------------------------------------------------ |
| `list`    | the page under investigation - everything                                            |
| `csv`     | the same rows through the same ORM with **no template**: the map's decisive contrast |
| `tagloop` | cost site 1 alone (`modelview/views.py:77-81`), replicated verbatim                  |
| `detail`  | one factsheet - production's other cheap probe                                       |

**Query count is the headline metric, not seconds.** It is exact, deterministic,
identical on a laptop and on the server, and it is what actually regressed: the
list page issues `7 x N + 2` queries because `model.tags.all()` sits inside
`{% for d in fields.values %}` and `MODEL_VIEW_PROPS` has seven top-level
entries. An `assertNumQueries` bound is therefore both the metric and the
regression test that would have caught this in 2025.

Seconds are recorded next to it because they are what the user feels, and
payload bytes because the third defect is a page that ships the whole dataset.

Note `tagloop`'s `bytes` column is not bytes: it is the number of rows the
OR-combined queryset returns - undeduplicated, so it equals the edge count.

## How the corpus is calibrated

Nothing here is invented; each number came from a cheap, read-only production
probe on 2026-09-01, and `profile.py` names the probe beside the number.

- **Column widths** - `field_profile.json`, the per-column mean character and
  word count over all 305 production models, from one 0.31 s request to
  `/factsheets/models/download/` (794,853 bytes, 305 x 192). Word count is the
  one that decides payload: `stringify` truncates every value to twelve words.
- **Tag distribution** - a 30-factsheet sample of detail pages (21 s of cheap
  requests). Sorted counts:
  `0 x11, 1, 1, 2, 2, 2, 2, 3, 3, 4, 4, 4, 5, 6, 7, 9, 9, 30, 696, 817`. Two of
  thirty carry a whole-tag-table snapshot, and those two hold 94% of all edges -
  which is why the corpus models a _mixture_ and not a mean.

The synthetic corpus is faithful in shape, not in content: every string is
nonsense of the right length.

## What it does not do

It does not reproduce production's absolute seconds - a laptop and the server
are different machines, and the harness talks to Django in-process with no
Apache, no `mod_wsgi` and no network. Read every number as a **ratio against the
same harness's baseline**, never as a prediction of production's clock.

Production keeps exactly one job: a single confirmatory `list` probe after a fix
ships, off-peak. Iterating there is what this harness replaces.
