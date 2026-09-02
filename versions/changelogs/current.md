<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

### Features

- Reproducible container deployment (Podman Quadlets): the whole OEP
  infrastructure - web app, PostgreSQL, Fuseki, Ontop and Lookup - is described
  as systemd Quadlet units on a shared container network, fronted by an nginx
  reverse proxy that terminates HTTPS on port 443. The application and Ontop
  images are self-provisioning (the OEO release, the OEO-extended template and
  the Ontop PostgreSQL JDBC driver are fetched/baked automatically); all
  credentials and host/HTTPS settings come from a single env file, and
  server-specific setup is scripted (`install.sh`, `install-nginx.sh`).
  [(#2319)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2319)

- Bulk upload observability: every upload attempt emits exactly one structured
  (logfmt) log line - table, user, outcome (success, validation-error,
  copy-error, size-cap, stall, embargo, busy), rows, bytes, and phase timings
  separating client transfer time from database-side COPY time and the
  id-sequence bookkeeping.
  [(#2362)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2362)

- Bulk upload guards: at most one running upload per user plus a configurable
  global cap (`BULK_UPLOAD_MAX_CONCURRENT`, default 2) - excess requests get
  HTTP 429 with Retry-After; uploads whose transfer rate falls below a
  configurable minimum are aborted (HTTP 408, recorded as a stall event); and
  the upload's database transaction carries statement and idle-in-transaction
  timeouts, so no client can pin a worker and an open transaction indefinitely.
  [(#2362)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2362)

- Bulk upload transport: gzip-compressed request bodies
  (`Content-Encoding: gzip`) are decompressed in streaming fashion straight into
  COPY, and a configurable cap on decompressed bytes per request
  (`BULK_UPLOAD_MAX_BYTES`, default 10 GiB) rejects oversized uploads and gzip
  bombs with HTTP 413 before they can exhaust disk or memory.
  [(#2362)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2362)

- Bulk load events: every authenticated, authorized bulk upload attempt -
  successful or failed - is recorded with user, table, status/error class, bytes
  received, and for successes the row count and the id range the rows landed in
  (the only provenance of bulk-loaded rows, and the handle for block-deleting a
  mistaken upload). Events are visible and filterable in the Django admin; the
  success response references the event.
  [(#2362)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2362)

- Bulk upload id contract: after an id-bearing upload the table's id sequence is
  advanced past the loaded ids (so subsequent row inserts cannot collide) and
  never moves backwards; uploads introducing ids above a generous sanity bound
  are rejected to protect the sequence for all writers of the table.
  [(#2362)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2362)

- Harden the bulk upload CSV contract: header preflight rejects duplicate,
  unknown, and missing required (NOT NULL without default) columns before the
  body streams; a UTF-8 BOM is stripped; empty fields are always NULL whether
  quoted or not; failure responses carry the CSV line number and column with the
  database's data-level message and never internal details.
  [(#2362)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2362)

- New bulk upload endpoint
  `POST /api/v0/tables/<table>/bulk-upload?delimiter=comma|semicolon|tab`:
  streams a CSV request body directly into the table via PostgreSQL COPY for
  fast ingestion of large datasets. Append-only and all-or-nothing; requires
  write permission, respects embargoes, and deliberately bypasses the per-row
  edit-journal (no row-level revision records for bulk-loaded rows).
  [(#2362)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2362)

- Redesign the OPR Summary tab as a condensed, grouped overview with per-state
  colored dots, comments, and clickable filters by review state.
  [(#2345)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2345)
- Dataset management UI, first slice: the user dashboard now opens on a
  dataset-first view with a switch to the familiar tables view. Users can see
  their own datasets and create new ones (name, title, description) without page
  reloads; invalid or taken names show inline errors. Creating tables without a
  dataset keeps working unchanged. The dataset API now reports duplicate names
  as a validation error instead of failing.
  ([#1971](https://github.com/OpenEnergyPlatform/oeplatform/issues/1971))

- Dataset quick actions on the dashboard: each dataset card can be edited inline
  (title and description; the name stays fixed) and deleted with a confirmation
  that makes clear the member tables are not deleted. Both actions update the
  page without reloads and are only available to the dataset creator.
  ([#1971](https://github.com/OpenEnergyPlatform/oeplatform/issues/1971))

- Dataset resource management on the dashboard: a manage panel per dataset lists
  the assigned tables (draft tables are badged, every entry links to its table
  page) and offers a search picker that only shows tables the user may assign -
  all published tables plus their own drafts and embargoed tables. Assigning and
  removing tables updates the panel without page reloads; data upload continues
  on the table pages.
  ([#1971](https://github.com/OpenEnergyPlatform/oeplatform/issues/1971))

- Public dataset list: the previously disabled "Datasets" toggle on the database
  table list is now active and shows a paginated card list of all datasets with
  name, description, resource count and the combined size of the member tables.
  Accessible without login; dataset detail pages follow in a later iteration.
  ([#1971](https://github.com/OpenEnergyPlatform/oeplatform/issues/1971))

- Add Dataset rest-api and metadata based concept as specified in oemetadata /
  frictionless
  ([#2071](https://github.com/OpenEnergyPlatform/oeplatform/pull/2071))
  - Resource metadata is stored for each created table.
  - Dataset objects can be listed, created, edited and existing tables can be
    assigned as resource
  - Datasets and assigned Resources are stored in the django database using a
    m:n relation with tables to read the oemetadata.
  - Rest api implementation
  - Datasets are creator-owned: creating one requires login and records the
    creator; only the creator can update, delete or assign tables. Reading
    datasets stays public.
  - Tables can be unassigned from a dataset again (new unassign endpoint).
    Assigning follows a curation model: any published table can be added to a
    dataset; draft tables and tables under an active embargo only by users with
    write permission on the table.
  - Dataset resource metadata is assembled live from the member tables on every
    read instead of being stored on the dataset, so it can no longer go stale
    after table metadata edits. Dataset names are slug-validated and fixed at
    creation (renaming would break URLs and references).

- Added eGon to the Open Data Tools section in the header navigation.
  ([#2300](https://github.com/OpenEnergyPlatform/oeplatform/issues/2300))

- OPR review-flow fixes: keep the category tabs usable in read-only/finished
  reviews, render the contributor General tab correctly, and make the category
  indicator dots, summary states, and auto-select reflect each round's pending
  actions for both reviewer and contributor.
  [(#2345)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2345)

- Fix navigation box during the OPR; show proper information and jump to next
  field that needs review. Hide start button for OPR if metadata is empty.
  [(#2310)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2310)

- Show comment in field when going to next field during OPR. Fix progress
  percentage and auto-select and -scroll to next field.
  [(#2342)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2342)

- Fix "Add data set" button in database section
  [(#2359)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2359)

- Fix Model/Framework factsheets silently dropping the 10th and later entries of
  array fields (e.g. Author(s)) on submit, caused by a regex that only matched
  single-digit field-name suffixes.
  [(#2365)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2365)

- Fix badge system; implement tier structure and bugfixes.
  [(#2361)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2361)

- Fixed the documentation workflow by correcting an invalid `mkdocstrings`
  reference to `TablePeerReviewContributorView`.
  [(#2360)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2350)

- Fix the oemetaBuilder Download button, which did nothing due to a
  `ReferenceError` under strict mode. The downloaded file now also gets a
  sensible name in the standalone tool instead of `undefined.metadata.json`.

- Fix nondeterministic resource order in the dataset metadata document: the
  resources list assembled live from a dataset's member tables is now ordered by
  table name (matching the dataset detail page) instead of database-dependent
  order, which also made a dataset detail test flaky on CI.
  ([#1971](https://github.com/OpenEnergyPlatform/oeplatform/issues/1971))

- Scenario Bundles: sector divisions and their sectors now load dynamically from
  the Open Energy Ontology (OEO) in the "Sectors and technology" tab of the
  bundle editor, replacing a hardcoded list - new divisions appear
  automatically. Selecting a division lists the sectors defined by it (resolving
  both ways the OEO models that membership), and the "Other" option opens the
  full OEO sector hierarchy, presented in a master-detail layout with the
  divisions on the left and their options on the right.

- Scenario Bundles: study descriptors are now populated from the OEO - every
  term the ontology marks as a study descriptor - instead of a hardcoded list,
  across the bundle editor, the bundle overview, the all-bundles filter, and the
  comparison board. Labels come straight from the ontology, so they stay in sync
  as the OEO evolves.

- Scenario Bundles: added a link to the external OEKG chat assistant
  (`https://oekg-chat.openenergyplatform.org/`) in the Scenario Bundles navbar
  dropdown and as a button on the bundles overview.

- Fix the Scenario Bundles overview table layout: the header defined one fewer
  column than each row (the expand-details column had no header) and the
  collapsible detail row over-spanned, leaving a ragged empty strip down the
  right-hand side.

- Make the Scenario Bundles overview toolbar responsive: on smaller screens the
  search / reset / compare buttons, the quick-search field, the view toggle and
  the create / OEKG-chat buttons now wrap onto their own rows instead of
  overlapping.

- Pin Vite to 8.0.13 for the frontend dev build. Vite 8.0.14-8.0.16 have a
  dependency-optimization regression that breaks the emotion/MUI setup in
  development ("init_emotion_react_esm is not defined", blank Scenario Bundles
  page); pinned to the last known-good release until it is fixed upstream
  ([vitejs/vite#22499](https://github.com/vitejs/vite/issues/22499)).

- Fix the `"as"` alias on fields of an advanced search request being parsed and
  then discarded: a labelled expression came back named after the expression
  (`ST_AsText_1`) or after its source column, breaking any client that keys
  results by column name. An invalid alias is now rejected instead of silently
  falling back to a generated name.

- Creating a table with a `FOREIGN KEY` or `CHECK` constraint no longer returns
  201 while silently dropping the constraint. The create path now rejects
  constraint types it cannot apply, naming the supported route: foreign keys are
  added after creation through the table endpoint, check constraints are not
  supported.

- Failed table creations and failed spatial queries now report the database's
  own reason instead of `Could not create table <name>` and `Invalid request`.
  An unusable column definition (`numeric(1001)`) and a reference system passed
  as a JSON string rather than a number (`"4326"` instead of `4326`, which makes
  PostGIS resolve `ST_Transform`'s projection-string overload) are both
  diagnosable from the response now. Causes that are not established as safe to
  disclose still report the generic message.
  ([openego/ding0#405](https://github.com/openego/ding0/issues/405))

- Geometry columns: an SRID declared in the column type (`geometry(Point,4326)`)
  is parsed as subtype and SRID instead of being passed through as one opaque
  string, and a non-numeric SRID is now rejected with a named error. The
  automatic GiST index on geometry columns and the registered subtype/SRID are
  now covered by tests, so a dependency upgrade cannot silently stop indexing
  new geo tables.

- Model/Framework factsheets: the tag editor no longer attaches every tag on the
  platform. Opening a factsheet for editing pre-checked all ~825 tags and showed
  them as already attached, so saving attached the lot - one database query per
  tag, which is what made "submit all" take minutes. The editor now shows only
  the tags that factsheet actually has, saving attaches exactly what was
  selected, and a save that fails validation comes back with the selection
  intact instead of discarding it. A save no longer wipes a factsheet's tags
  when the form is submitted without the tag widget. New: a "remove all tags"
  button and a live count of the selection on the Tags tab.
  [(#2385)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2385)
  [(#2381)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2381)

- Model/Framework factsheet overview: the sidebar tag filter now lists each tag
  actually in use by that sheet type exactly once, in name order, instead of one
  checkbox per tag _attachment_ - on production 12,156 checkboxes for 825
  distinct tags, 6 MB of the page. The frameworks page previously offered 290
  tags where only 71 were in use, so 219 of its checkboxes returned no results
  when clicked.
  [(#2346)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2346)

- Model/Framework factsheet overview: the active tag filter is now kept in the
  page URL (`?tags=<tag>,<tag>`), so a filtered view can be reloaded, bookmarked
  and shared, and returning to such a URL restores the checked tags. This also
  fixes the "Download CSV" link silently returning a file with only a header row
  whenever a tag filter was applied: the page sent a prefixed value the download
  endpoint did not recognise, so it matched nothing and reported no error. Links
  in the old format keep working.
  [(#2346)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2346)

- Deleting a Model/Framework factsheet is now restricted to administrators, and
  refused by the server rather than only hidden in the page. The delete button
  and the edit link were rendered on every factsheet page with no permission
  check at all, so any registered account could irreversibly destroy any of the
  339 factsheets in one click, with no record of who did it. Anonymous visitors
  are no longer shown edit and delete buttons they cannot use. Editing stays
  open to every logged-in account, as intended. Every factsheet create, update
  and delete now leaves one structured log line.

## Documentation updates

- New "Production deployment (Podman)" guide (Overview → Install → Ontop →
  Update → Maintenance) in the project docs, canonical for the rootless
  Podman/Quadlets production path. The podman READMEs now point at it, the
  docker/compose docs are marked development/CI-only, and stale/duplicate
  deployment docs were consolidated (retired the orphan ontop page, fixed broken
  links, reconciled the stated Postgres version, added missing SPDX headers).
  [(#2319)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2319)

- Updated the OE Family Steering Committee
  [#2332](https://github.com/OpenEnergyPlatform/oeplatform/pull/2332)

- New Scenario Bundles architecture & developer guide in the project docs
  (Documentation → Features → Scenario Bundles), mapping how the React frontend,
  the Django `factsheet` app, the OEKG (Fuseki) and the OEO ontology fit
  together, with the request/data flow and which form-field lists are
  OEO-driven; the top-level `oekg` app README was expanded to match.

## Code Quality

- Refactor the OPR feature: backend service layer (`ReviewService`) with
  append-only review rounds + projection, a shared template partial removing
  reviewer/contributor duplication, and the `peer_review` JS reorganized into
  `core/` `roles/` `ui/` modules.
  [(#2345)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2345)
