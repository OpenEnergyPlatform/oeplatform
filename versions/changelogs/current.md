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

- Advanced API: a session that no request has used for 10 minutes is now closed
  even when it still has an open cursor, so an abandoned session no longer holds
  its place in the connection limit until the server restarts. A session a
  request is still using, a long download included, is never closed. Closing or
  rolling back a session that is already gone now answers success instead of
  being refused at the connection limit. The 10 minutes are the new optional
  setting `CURSOR_TIME_OUT` (#2734)

## Documentation updates

- The documentation Home now says what the OEP is and guides every visitor to
  the right resource: understanding the OEP and the Open Energy Family, using
  the platform, using the API, or installing and developing. The Installation
  page guides between the development and the production install

## Code Quality
