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
