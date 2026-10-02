<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2026 Hendrik Huyskens <https://github.com/henhuy> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

- The Django database port can be set with `OEP_DJANGO_PORT` in the
  `securitysettings.py` template, like the OEDB's `LOCAL_DB_PORT`. Without it a
  local database container could not be published on any port but 5432
  [(#2581)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2581)
- The dev image caches pip downloads and built wheels in a BuildKit cache mount
  instead of discarding them. A single new line in `requirements.txt` used to
  re-download and re-compile all ~47 packages, several minutes of it building
  `psycopg2`, `shapely` and `owlready2` from source. The image stays the same
  size, because the cache lives outside it
  [(#2436)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2436)
- Refactor user groups into organizations; add fields to the organization model;
  refactor HTMX for organization management pages
  [(#2261)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2261)

## Features

- The tables tab of the profile dashboard shows one list instead of the draft
  and published card sections: every Table you can write, directly or through an
  organization, with its status and where your access comes from. A status
  segment with counts, a search, sorting, 25 rows per page and the whole state
  in the address bar. Publishing, unpublishing and deleting moved into each
  row's ⋯ menu (#2561, #2562)
  [(#2572)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2572)
- Each row of the tables tab now says whether the Table would pass the publish
  check (with the reasons and links to fix it on click, published Tables
  included), its review state with the badge linked to the review, how many
  datasets it is in (yours first, never another user's draft) and its topics.
  The list sorts by review state and by dataset count too
  [(#2554)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2554)
- The tables tab filters by review state, by where your access comes from
  (direct or one of your organizations), by dataset (in any, in none, or one),
  and behind "More filters" by topic (any of) and tags (all of). Options come
  from your own tables only. Active filters show as removable chips with "Reset
  all", and a value from an old link that no longer applies shows as a muted
  chip instead of emptying the list
  [(#2556)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2556)
- The tables tab fits its width without sideways scrolling, from a wide screen
  to a phone: as the list narrows, Topics drops first, then Review and Datasets,
  and on the narrowest screens each row stacks into two lines with a "Sort by"
  select in place of the column headers. Where the filter bar does not fit on
  one line, everything but the search folds behind "Filters (n)". Long
  organization names are shortened in the Access column, in full on hover
  [(#2555)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2555)
- Whether a Table passes the publish check is now stored with it and recomputed
  on every metadata write, so the tables tab filters by "Publishable" and sorts
  by it (not publishable first). Publishing itself still checks the metadata at
  that moment. Deploy: run `python manage.py migrate`, then
  `python manage.py recompute_publish_gate --apply` once; until it has run, the
  Publishable filter matches no existing Table
  [(#2560)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2560)
- Every row of the tables tab has a ⋯ menu: edit metadata, upload data, and
  publish (topic and embargo in a dialog) or unpublish, without a page reload or
  an alert. An action above your role on that table stays in the menu, disabled,
  with the reason. The dialog says first what would be left out and why; the
  server checks again and changes nothing if anything changed in between. The
  list then refreshes itself, keeping its filters, and a message says what
  happened. Each action writes one log line per table
  [(#2561)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2561)
- A Table now records when its content last changed, its data (rows, a bulk
  upload, columns and constraints) and its metadata separately. Publishing,
  unpublishing, embargoes and role changes do not count. The tables tab shows
  the later of the two in a new Modified column, sorts by it by default (newest
  first, tables with no recorded change last) and filters by a Modified date
  range under "More filters". Nothing was recorded before this release, so
  existing tables show "–" until they next change. Deploy: run
  `python manage.py migrate` (`dataedit.0056`, two empty columns)
  [(#2557)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2557)
- Existing tables get the data half of their Modified date where one can be
  recovered: the latest applied change in their edit journal or their latest
  successful bulk upload, whichever is later. The new command
  `python manage.py backfill_data_modified` is a dry run that counts what it
  found; with `--apply` it fills only tables that have no date yet, so a date
  stamped since the release is never overwritten and a second run changes
  nothing. It only reads the OEDB, and never creates a missing journal. The
  metadata half stays empty, because no metadata save was ever timestamped.
  Deploy: run it once after `dataedit.0056`
  [(#2589)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2589)
- The tables tab's ⋯ menu adds a table to one of your own datasets, or removes
  it from one (offered only when one of yours holds it). A draft or embargoed
  table may be added by anyone holding Data editor on it, directly or through an
  organization: before, a draft you could write only through an organization was
  offered on the Datasets tab and then refused. The dataset assign API and the
  Datasets tab follow the same rule, and the API's assign and unassign now
  change all the named tables or none
  [(#2563)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2563)
- Tables can be deleted from the ⋯ menu of the tables tab again, published ones
  included (Data maintainer or above). A draft asks for a plain confirmation.
  For a published table the dialog says what deleting breaks (the datasets it
  leaves, other people's named with their owner, its review state, an active
  embargo, and that links from scenario bundles stop resolving) and asks you to
  type the table's name. A batch holding a published table or more than ten is
  confirmed by typing the number of tables, and at most 50 are deleted at once.
  If the database table cannot be removed after the table's record is gone, a
  warning that stays on screen names it, and the log says `drop=failed`
  [(#2562)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2562)
- A table's Access cell, or "Manage access" in its ⋯ menu, opens a side drawer
  listing who holds which role (Data editor, Data maintainer, Admin), your own
  entries marked. A Table admin adds a person or one of their own organizations
  with a role in one step, changes or removes any holder; everyone else sees the
  list read-only with the table's Admins, and anyone with a role of their own
  can leave the table. Organizations go up to Data maintainer, Admin is given to
  people by name, and a table always keeps one person with Admin. Losing your
  own Admin, or the table from your dashboard, asks once. The drawer stays open
  while the list refreshes behind it; each change writes one log line with the
  role before and after
  [(#2566)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2566)

## Bugs

- Finishing a peer review now writes the merged metadata the way every other
  metadata write does: it is validated, and the table's displayed title and its
  search entry follow the accepted values. Before, a review that accepted a new
  title left the old one on the table page and in lists, and the search kept
  finding the pre-review words. A merge that fails validation is refused with a
  readable message and writes nothing: the review stays unfinished, and no badge
  or "reviewed" flag is set
  [(#2552)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2552)
- The table page no longer stores a new saved view on every visit. Production
  had collected ~195,000 of them, scanned twice per page view. A migration
  removes the empty copies and adds a unique constraint on (table, type, name),
  which keeps them out and indexes the lookup; saved views that carry filters or
  options are never deleted, and if two of them share a name, one is renamed
  "name (id)". Saving a view under a name the table already uses now says so
  instead of failing, a graph marked as default no longer replaces the Table
  tab, and setting the default view or deleting a view requires POST
  [(#2218)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2218)
- The docker development setup works on macOS: bind-mounted folders are given to
  the container user by numeric id (macOS' group id already exists in the image,
  so the named group was never created), and a `.DS_Store` left by Finder no
  longer stops the OEO version lookup, the ontology module list or the about
  page. The build context now leaves out `.git/`, `static/`, `data/` and cache
  files at any depth, which also applies to the production images
  [(#2344)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2344)
- Deleting a peer review now checks the caller: only its reviewer or a platform
  admin may delete it
  [(#2544)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2544)
- Restrict profile pages to their owner and check organization permissions
  before saving
  [(#2547)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2547)

## Documentation updates

## Code Quality
