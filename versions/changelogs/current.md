<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

- Reworked the OEO Viewer using React and the
  [TSS Widgets library](https://ts4nfdi.github.io/terminology-service-suite/comp/latest/?path=/docs/overview--docs),
  providing enhanced usability.
  [(#2222)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2222)
- Shifted OEO Viewer data retrieval to the
  [TIB Terminology Service](https://terminology.tib.eu/ts) (OLSv4 backend),
  significantly reducing future maintenance efforts by leveraging
  NFDI-maintained widgets.
  [(#2222)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2222)

## Removed

- Removed the legacy custom backend and frontend implementation of the OEO
  Viewer. [(#2222)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2222)

## Features

### Bugs

## Documentation updates

## Code Quality
