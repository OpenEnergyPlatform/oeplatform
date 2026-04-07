<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

- Create tables_sections.html, delete user_partial_tables
  [(#2248)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2248)

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

## Documentation updates

## Code Quality
