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

## Documentation updates

- Updated the OE Family Steering Committee
  [#2332](https://github.com/OpenEnergyPlatform/oeplatform/pull/2332)

## Code Quality

- Refactor the OPR feature: backend service layer (`ReviewService`) with
  append-only review rounds + projection, a shared template partial removing
  reviewer/contributor duplication, and the `peer_review` JS reorganized into
  `core/` `roles/` `ui/` modules.
  [(#2345)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2345)
