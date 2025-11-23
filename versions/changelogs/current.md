<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

- changes to urls:
  - `/dataedit/*` -> `/database/*`
  - `/api/v0/schema/<SCHEMA>/tables/*` -> `/api/v0//tables/*` (but old urls
    still supported)

## Features

## Bugs

- Order columns present in column api endpoint by the ordinal position (which
  was specified when creating the table)
  [(#2176)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2176)
- fixing #2173 graph view, and also lon lat map view which was not fully
  implemented before

## Documentation updates

## Code Quality

- harmonized all api endpoints
  - names
  - validate existing table objects instead of passing table names
  - remove schema argument from views
