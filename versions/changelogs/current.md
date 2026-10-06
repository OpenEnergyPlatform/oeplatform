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

- Speed up the row upload API: index the unapplied rows of the edit-journal meta
  tables (`_<table>_insert/_edit/_delete`, back-filled by an oedb migration),
  mark applied rows with one set-based update instead of a per-row OR chain,
  scan only the meta table relevant to the operation, and apply changes exactly
  once per request instead of twice. Also fixes applying a journal that held
  pending changes of more than one kind: the first change of each new kind was
  dropped and the apply then failed. The oedb migration builds the index for
  existing meta tables one at a time, so it neither write-locks all journals at
  once nor overflows Postgres' lock table on a large platform.
  [(#2362)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2362)
- For API clients: `tables/<table>/move_publish/<topic>/`, `unpublish/` and
  deleting a table now take the same path as the tables tab, with the same
  request and response bodies (`{}`, or `{"reason": …}` on a refusal) and one
  log line per call (`via=api`). Publishing writes everything or nothing: an
  unknown topic used to set the embargo before failing with "Invalid request",
  and now answers 400 naming the topic with nothing changed. Two requests that
  used to succeed now answer 400 with the reason: publishing under `draft` (a
  status, not a topic), and an embargo duration other than `none`, `6_months` or
  `1_year` (it used to be ignored). A missing open data license is still a 400,
  worded as the tables tab words it ("Fails the Publish gate: License").
  Unchanged: a published table can be published again under another topic, an
  omitted embargo leaves the existing one as it is, unpublishing a draft
  succeeds, and a published table can be deleted. If a table's record is deleted
  but its database table cannot be dropped, the delete answers 500 naming the
  table instead of 400 "Invalid request"
  [(#2569)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2569)
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
- Changing an account's email address at `/accounts/email/` now asks for the
  password again, as a password change already does. The previous address gets a
  mail when the address changes, and an account keeps one address: a new one
  replaces it once it is confirmed
  [(#2609)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2609)

## Features

- A Table's Holders can be managed through the REST API:
  `GET`/`POST /api/v0/tables/<name>/permissions/` lists them and adds one, and
  `PATCH`/`DELETE .../permissions/user:<id>/` (or `org:<id>/`) changes or
  removes one. Every write goes through the same permission service as the
  access drawer, so every rule holds there too, and logs `via=api`. A change
  that takes your own Admin away answers `409` until it is sent again with
  `confirm`
  [(#2570)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2570)

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
- A Table now records when it was created, and the tables tab shows it in a new
  Created column, sortable (unknowns count as the oldest) and filterable by a
  Created date range under "More filters". Tables created before November 2025
  read "before Nov 2025": the field they used to be dated by (`date_updated`)
  holds a date their metadata declared, not when they were created, and no
  record of that exists. Such a table matches a Created range only with no start
  and an end on or after 30 Oct 2025, the only ranges that certainly hold it.
  `date_updated` itself is unchanged. Deploy: run `python manage.py migrate`
  (`dataedit.0057`, one column, filled from `date_updated` for tables above id
  69915 only, measured on production)
  [(#2559)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2559)
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
- Tables in the tables tab can be selected and published or unpublished in one
  go. Each row has a checkbox, the header ticks the page, Shift+click ticks a
  range, and "Select all N matching tables" takes every table under the current
  filters across all pages. The selection survives paging, sorting and actions,
  and is cleared, with a note, when the filters or the search change. A bar
  above the list shows how many are selected; its place is kept while nothing
  is, so the list does not move on the first tick. Publish takes one topic and
  embargo for the whole batch and leaves out, by name and with the reason,
  tables already published, tables failing the publish check and tables you are
  not Table admin of. Unpublish names other people's datasets that will then
  hold a draft. At most 1,000 tables are published or unpublished at once, and a
  batch is done whole or not at all
  [(#2564)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2564)
- The selection bar of the tables tab can also delete the selected tables and
  add them to, or remove them from, one of your own datasets. Bulk delete lists
  every table, marks the published ones and counts what deleting breaks: how
  many are published, reviewed or under embargo, which datasets lose how many of
  them (other people's with their owner), and the links from scenario bundles
  that stop resolving. A batch holding a published table or more than ten is
  confirmed by typing the number of tables, at most 50 at once, and every table
  whose database table could not be removed is named in a warning that stays on
  screen. Choosing the dataset re-checks the selection on the spot and names the
  tables already in it (add) or not in it (remove); at most 2,500 tables are
  added or removed at once, all or none
  [(#2565)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2565)
- Tables tab: the bulk bar can share the selected tables with one of your
  organizations as Data editor or Data maintainer, or remove an organization
  from them. A share only ever raises a role: tables where the organization
  holds that role or more already stay unchanged and are named. A removal leaves
  out the tables where the organization's old Admin grant is the only Admin
  ("give someone Admin there first") and names the tables you would lose access
  to before you confirm. Both dialogs state the organization's member count,
  re-check the selection as you choose, leave out tables you are not a Table
  admin on, and write all tables or none, at most 2,500 at once, with one log
  line per table changed
  [(#2568)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2568)
- Tables tab: a bulk dialog's title counts what its list counts, the tables the
  action acts on, and says out of how many were selected ("Delete 14 of 16
  tables", "Will be deleted (14)", "Left out (2)"). The dialogs name datasets by
  their title, and unpublish says how many of the tables each of other people's
  datasets holds. Where the rows stack on a narrow screen, "Select this page"
  selects and clears the visible page and offers "Select all N matching tables",
  as the header checkbox does on a wider one
  [(#2596)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2596)
- REST API: share many tables with one of your organizations, or remove an
  organization from many tables, in one request, under the same rules as the
  dashboard's bulk bar: all tables or none, a share only raises a role, a
  repeated removal succeeds, at most 2,500 tables at once
  (`POST /api/v0/organizations/<id>/table-permissions/share/` and `…/remove/`).
  And everywhere a table's access is managed (the access drawer, the table's
  permission page, the API), removing or lowering an organization's old Admin
  grant that is the table's only Admin is now refused instead of leaving the
  table with no Admin at all
  [(#2595)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2595)

## Bugs

- Errors on the sign-up, set-password and reset-password forms are shown as
  errors (red) instead of green "success" alerts, and the reset-password form
  shows its errors at all: it looked for them on a field it does not have.
  `securitysettings.py.default` no longer lists a login provider with an empty
  `provider_id`, which made the sign-in and sign-up pages fail on a fresh setup
  [(#2608)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2608)
- Saved table views (graph and map views, the default view) can only be created,
  changed or deleted by someone with write permission on the table; the "Add …
  view" links are shown only to them. Saving a view now finds it only within its
  own table
  [(#2601)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2601)
- Running the test suite no longer deletes your own tables. The tests used the
  data database configured for the platform, and one of them clears its whole
  sandbox schema, which took the dev container's example table with it while its
  record stayed behind (the metadata editor then showed it without columns). A
  test run now uses a data database of its own, `test_<name>` or
  `LOCAL_TEST_DB_NAME`, which the test runner creates and migrates. And
  `create_example_tables` now leaves a complete example table however often it
  runs: it repairs a record whose table is gone, seeds the schema the table is
  really in (it never had its 4 rows before), and no longer fails to create its
  fallback user
  [(#2602)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2602)

- Deleting a table removes its peer reviews with it. A review names its table
  only by name, so a table created later under the same name used to inherit the
  old review state and badge. Dropping a deleted table's database tables now
  gives up after waiting 1 s for another session's lock instead of waiting until
  the request times out; it is then reported as a table that could not be
  removed, as any failed drop is
  [(#2597)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2597)
- The metadata editor no longer hangs on a table whose column carries a very
  long annotation list. A column with 4,525 value references never finished
  loading, because the form library's cost grows with the square of a list's
  length. Lists over 200 entries are now kept out of the form with a notice
  saying so, and are saved and downloaded unchanged, together with any entries
  added in the form
  [(#2593)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2593)

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
- A table's permission page follows the same rules as the dashboard's access
  drawer: adding a person or organization takes a role in the same step, "None"
  is no longer offered, organizations go up to Data maintainer and can be added
  only by their members, a table always keeps one person with Admin, and losing
  your own Admin asks once. A refused change is shown as a message on the page
  and writes nothing; before, an unknown user name was a server error, any
  number was stored as a level, and the last Admin could remove themself. Each
  change writes one log line (`via=table-page`). Error messages across the site
  are now shown in red
  [(#2567)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2567)

## Documentation updates

- Reworked the pull request template: sections for testing, deploy notes and a
  new "For reviewers" block; the changelog line is now written only in the
  changelog; fixed the broken reviewer-guidelines link
  [(#2603)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2603)

## Code Quality
