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

- Fix Model/Framework factsheets silently dropping the 10th and later entries of
  array fields (e.g. Author(s)) on submit, caused by a regex that only matched
  single-digit field-name suffixes.
  [(#2365)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2365)

- Fix badge system; implement tier structure and bugfixes.
  [(#2361)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2361)

- Fixed the documentation workflow by correcting an invalid `mkdocstrings`
  reference to `TablePeerReviewContributorView`.
  [(#2360)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2350)

## Documentation updates

- Updated the OE Family Steering Committee
  [#2332](https://github.com/OpenEnergyPlatform/oeplatform/pull/2332)

## Code Quality

- Refactor the OPR feature: backend service layer (`ReviewService`) with
  append-only review rounds + projection, a shared template partial removing
  reviewer/contributor duplication, and the `peer_review` JS reorganized into
  `core/` `roles/` `ui/` modules.
  [(#2345)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2345)
