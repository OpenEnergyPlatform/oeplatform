<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Features

- Add a new OEO search page for simple search and browsing of OEO entities
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)
- Add interactive parent/child hierarchy navigation and IRI copy functionality
  to entity detail pages
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)

## Changes

- Reworked the former OEO Class pages into OEO Entity pages, now supporting
  details for Classes, Properties, and Individuals
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)
- Integrated NFDI4Energy Terminology Service Suite (TSS) React widgets for
  standardized search, metadata, and relations displays
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)
- Improved IRI resolution to seamlessly handle and route external/imported
  ontology terms (e.g., OBO Foundry)
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)
- Implemented client-side React routing (SPA) for seamless transitions between
  search results and entity details
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)

## Removed

- Removed the previous custom backend and frontend implementation for the OEO
  Class / IRI pages
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)

## Bugs

## Documentation updates

## Code Quality
