<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# What is this app used for?

The OEKG django app is used to encapsulate functionality to interact with the
OEKG within the OEP. If one needs such functionality in another django app like
`api` then the oekg app should be imported there. New functionality should also
extend the oekg app.

This includes variables and functions to connect to databases (like Jena Fuseki)
and to access or edit its content. The main libraries used here are rdfLib
(broadly used in the factsheet app to create scenario bundles) and the
SPARQLWrapper to formulate a Query as a string. The latter approach is more
efficient as it avoids parsing data (like the Graph) to python data types.

## What's in here

- `sparqlQuery.py` — the reusable SPARQL query/update functions against the OEKG
  (bundle filters, factsheet listings, and the composable WHERE-clause helpers).
- `sparqlModels.py`, `views.py`, `urls.py` — the Django surface, including the
  YASGUI SPARQL explorer (`oekg:main`).

The low-level connection setup — the `SPARQLWrapper` clients (`sparql`,
`update_endpoint`) and the in-memory OEO ontology graph (`oeo`, `oeo_owl`) —
lives in `factsheet/oekg/connection.py` and is imported here.

## Two things are called `oekg`

- **This app** (`oekg/`, repo root) — reusable OEKG query functionality. Extend
  it when you add new ways to read or write the graph.
- **`factsheet/oekg/`** — an internal package of the `factsheet` app that holds
  the connection setup this app builds on. Not a Django app.

## Related documentation

The main consumer of the OEKG is the **Scenario Bundles** feature. For how the
frontend, Django, OEKG and OEO layers fit together, see the
[Scenario Bundles architecture guide](../docs/oeplatform-code/features/scenario-bundles/architecture.md).
