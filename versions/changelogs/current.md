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

- Build search field to search in the user's tables
  [(#2248)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2248)

- Update the Graph Vie WIdget on the OEO Viewer page and enable the graph
  comparison feature
  [(#2277)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2277).

- Add a Option to select the Language on the OEO Entity Pages. This only shows
  the german / english synonym if available for an entity
  [(#2277)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2277).

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
- The metadata api now also syncs the data schema documented in the metadata
  with the table schema available in the database
  [(#2290)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2290)

- Add new java script functionality for enhanced fetching of additional
  information from table metadata and reworked table listing UI to show table
  listing cards with additional information
  [(#2311)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2311)

### Bugs

- Reviewer&Contributor page: calculation of percentage of progress of reviewed
  fields takes into account empty fields
  [(#1386)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1386)

- Refactored the OEO Viewer layout to better organize hierarchy, metadata, and
  graph widgets, including improved mobile responsiveness and also adapt to the
  oeo inferred version which is now served by the TIB-TS (OLSv4 System)
  [(#2237)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2277).

- Update the Hierarchy Widget to Expand and highlight the currently selected
  Entity in the OEO Viewer
  [(#2237)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2277).

- On the OEO Entity page the Entity type is now automatically detected to stream
  line the user experience as users do not have to check the type manually - we
  now also show the type of the entity
  [(#2237)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2277).

- Fixed a bug in the TIB-TS api when the user navigates to ObjectProperties /
  Individuals. The API path is now correctly set
  [(#2237)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2277).

- Reviewer&Contributor page: calculation of percentage of progress of reviewed
  fields takes into account empty fields
  [(#1386)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1386)

- Cleanup incomplete updates to the OpenPeerReview. Some parts of the code are
  incomplete due to a messi code refactoring where some code snippets have been
  lost due to merge conflicts in commits that are not pushed to remote.
  [(#2289)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2289)

- Fixed a bug in the oemetaBuilder tool that removed `isAbout` and
  `valueReference` entries and added unwanted properties when the users submits
  the Editor form
  [(#2290)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2290)

- Fixed a bug in OEO loading module that was made visible by OEO version 2.12.0
  as there was a new metadata owl file introduced which can not be parsed with
  rdflib [(#2311)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2311)

- Fix navigation box during the OPR; show proper information and jump to next
  field that needs review. Hide start button for OPR if metadata is empty.
  [(#2310)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2310)

## Documentation updates

## Code Quality
