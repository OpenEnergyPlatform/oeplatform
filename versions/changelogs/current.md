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

- The OEKG scenario-bundle REST API: `POST /api/v0/scenario-bundles/` creates a
  bundle and `GET /api/v0/scenario-bundles/<uid>/` reads it back. The server
  mints the identifier, the acronym is enforced unique, the bundle is validated
  against the canonical SHACL shape **before** anything is written, and the
  write is one atomic request. Reads are public; writes need authentication
  [(#2430)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2430)

- The OEKG REST API gets its own transport to the graph store
  (`oekg/graph_store.py`): one SPARQL request per write, which Fuseki treats as
  one transaction, instead of one committed request per triple. Its tests run
  against a real store in an isolated named graph, and skip with a stated reason
  when no store is reachable
  [(#2429)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2429)

- `python manage.py fetch_oekg_shapes` obtains the canonical OEKG SHACL shape
  from a pinned revision of the `oekg` repository, and generates the
  `rdfs:label` subset validation needs from the OEO release already on disk
  [(#2428)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2428)

## Bugs

- The generated OEO label subset copied labels verbatim, so 1,855 of 2,058
  carried an `@en` tag and four terms carried two labels. The shape requires
  `sh:datatype xsd:string` and `sh:maxCount 1` on `rdfs:label`, and a
  language-tagged literal is `rdf:langString` — so every picked OEO term failed
  validation. Labels are normalised to one plain string per term
  [(#2430)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2430)

- The OEKG SPARQL endpoint test patched `oekg.utils.execute_sparql_query` while
  the view binds that function into its own namespace, so the mock never took
  effect and the test made a real network call to a host that only resolves
  inside the compose network. It failed on every local run. Patched at the right
  name, it is now hermetic
  [(#2429)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2429)

## Documentation updates

## Code Quality
