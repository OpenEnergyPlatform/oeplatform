<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

- tables per topic are paginated
- OEP admin users now can edit scenario bundles
  ([#2103](https://github.com/OpenEnergyPlatform/oeplatform/pull/2103))
- Rework oeo-view app using the
  [Terminology Service Suite Widget library](https://ts4nfdi.github.io/terminology-service-suite/comp/latest/?path=/docs/overview--docs)
  using the [TIB-Terminology Service API](https://api.terminology.tib.eu/api/)
  to query the OEO contents
  [(#2105)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2105)

## Features

- new api endpoint to unpublish table

## Bugs

- #2136: new tables cannot add tags

## Documentation updates

## Code Quality

- all apps have cleaned up `views.py` and `urls.py` with names for reverse
  lookup
- all apps have minimal tests some of those views
- reverse lookup instead of hardcoded urls in frontend and backend
