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
- Deleting a peer review now checks the caller: only its reviewer or a platform
  admin may delete it
  [(#2544)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2544)
- Restrict profile pages to their owner and check organization permissions
  before saving
  [(#2547)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2547)

## Documentation updates

## Code Quality
