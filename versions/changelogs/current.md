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
  in the address bar. Until the row actions follow (#2561, #2562), publishing,
  unpublishing and deleting are not offered on the dashboard
  [(#2572)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2572)

## Bugs

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
