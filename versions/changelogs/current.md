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

## Features

## Bugs

- A table download through the API (`.../rows/`) that the client stops reading
  gives its database connection back straight away. It used to hold the
  connection, a transaction and a lock on the table until Python's garbage
  collector next ran, which on production took up to an hour and more
  [(#2735)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2735)

## Documentation updates

- The documentation Home now says what the OEP is and guides every visitor to
  the right resource: understanding the OEP and the Open Energy Family, using
  the platform, using the API, or installing and developing. The Installation
  page guides between the development and the production install

## Code Quality
