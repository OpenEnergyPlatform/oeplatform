<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

- Speed up the row upload API: index the unapplied rows of the edit-journal meta
  tables (`_<table>_insert/_edit/_delete`, back-filled by an oedb migration),
  mark applied rows with one set-based update instead of a per-row OR chain,
  scan only the meta table relevant to the operation, and apply changes exactly
  once per request instead of twice. Also fixes a bug where the first change of
  each type was dropped when a meta table held mixed pending change types.
  [(#2362)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2362)

## Features

- Redesign the OPR Summary tab as a condensed, grouped overview with per-state
  colored dots, comments, and clickable filters by review state.
  [(#2345)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2345)

## Bugs

- OPR review-flow fixes: keep the category tabs usable in read-only/finished
  reviews, render the contributor General tab correctly, and make the category
  indicator dots, summary states, and auto-select reflect each round's pending
  actions for both reviewer and contributor.
  [(#2345)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2345)

- Fix navigation box during the OPR; show proper information and jump to next
  field that needs review. Hide start button for OPR if metadata is empty.
  [(#2310)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2310)

- Show comment in field when going to next field during OPR. Fix progress
  percentage and auto-select and -scroll to next field.
  [(#2342)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2342)

  - Fixed the documentation workflow by correcting an invalid `mkdocstrings`
    reference to `TablePeerReviewContributorView`.
    [(#2360)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2350)

## Documentation updates

- Updated the OE Family Steering Committee
  [#2332](https://github.com/OpenEnergyPlatform/oeplatform/pull/2332)

## Code Quality

- Refactor the OPR feature: backend service layer (`ReviewService`) with
  append-only review rounds + projection, a shared template partial removing
  reviewer/contributor duplication, and the `peer_review` JS reorganized into
  `core/` `roles/` `ui/` modules.
  [(#2345)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2345)
