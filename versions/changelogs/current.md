<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Highlights

<!--
Three to five short points for users, shown on the platform's "What's new"
page (base:whats-new) and linked from the homepage, without the version number.
Plain words, no internals. Left empty (as in a patch release), the page keeps
the previous release's highlights.
-->

## Changes

- Django REST framework is updated from 3.17.2 to 3.18.2, which brings three
  security fixes. One effect is visible in the scenario bundle API: a validation
  error inside a list (scenarios, study reports, dataset links, authors,
  regions, ...) now names the entry it belongs to by its position,
  `{"scenarios": {"1": {...}}}`, instead of a list holding an empty object for
  every valid entry
  [(#2737)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2737)

## Features

## Bugs

## Documentation updates

- The documentation Home now says what the OEP is and guides every visitor to
  the right resource: understanding the OEP and the Open Energy Family, using
  the platform, using the API, or installing and developing. The Installation
  page guides between the development and the production install

## Code Quality
