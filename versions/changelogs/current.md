<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

## Features

- Add Dataset rest-api and metadata based concept as specified in oemetadata /
  frictionless
  ([#2071](https://github.com/OpenEnergyPlatform/oeplatform/pull/2071))
  - Resource metadata is stored for each created table.
  - Dataset objects can be listed, created, edited and existing tables can be
    assigned as resource
  - Datasets and assigned Resources are stored in the django database using a
    m:n relation with tables to read the oemetadata.
  - Rest api implementation

## Bugs

- Reviewer&Contributor page: calculation of percentage of progress of reviewed
  fields takes into account empty fields
  [(#1386)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1386)

## Documentation updates

## Code Quality
