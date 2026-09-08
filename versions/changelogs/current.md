<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

## Features

- Add `python manage.py fetch_oekg_shapes`, the single seam through which the
  platform obtains the canonical OEKG SHACL shape (from a **pinned** revision of
  the `oekg` repository) and the small `rdfs:label` subset validation needs
  (generated from the OEO release already on disk -- the ontology itself is
  never downloaded again). Both artifacts land in the gitignored `shapes/`
  directory and are baked into the Docker and Podman images at build time. An
  unpinned or moving revision is refused, because an unpinned fetch would change
  the validator without a deploy.

## Bugs

## Documentation updates

## Code Quality
