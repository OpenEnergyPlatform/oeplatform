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
- `shape_artifacts.py` + `management/commands/fetch_oekg_shapes.py` — the single
  seam through which the platform obtains the canonical SHACL shape for scenario
  bundles and the `rdfs:label` subset validation needs. See below.

The low-level connection setup — the `SPARQLWrapper` clients (`sparql`,
`update_endpoint`) and the in-memory OEO ontology graph (`oeo`, `oeo_owl`) —
lives in `factsheet/oekg/connection.py` and is imported here.

## The shape and the label subset

The OEKG REST API validates a bundle against the canonical SHACL shape that
lives in the [`oekg` repository](https://github.com/OpenEnergyPlatform/oekg),
not against a copy in this repo. One management command obtains it:

```bash
python manage.py fetch_oekg_shapes
```

It writes two files into the gitignored `shapes/` directory:

| File              | Where it comes from                                        |
| ----------------- | ---------------------------------------------------------- |
| `oekg_shapes.ttl` | fetched from `oekg` at a **pinned** revision               |
| `oeo_labels.ttl`  | generated from the OEO release already under `ontologies/` |

Three things about it are deliberate:

- **The revision is pinned and an unpinned one is refused.** The URL is built
  from a repository, a `PinnedRef` and a path, so a branch URL cannot be passed
  in at all; `--tag latest` and friends are rejected with an error. An unpinned
  fetch would change the _validator_ without a deploy.
- **The full ontology is never fetched.** `ex:CommonShape` needs exactly one
  `rdfs:label` on every OEO term a bundle picks — but only the labels. The
  `rdfs:label`-only subset is ~2,000 triples and under 200 KB, against 1.3 GB
  resident and ~36 s to parse `oeo-full.owl`. So the command reads the release
  that is already on disk and extracts from it.
- **A failed fetch leaves the previous artifact usable.** The body is parsed and
  checked to be a shape graph before anything is written, and the write itself
  is a rename — so an error page or a truncated response never becomes "the
  validator".

To move the shape, bump `OEKG_SHAPES_PINNED_COMMIT` in `oeplatform/settings.py`
and redeploy. The image builds (`docker/Dockerfile`, `podman/Dockerfile`) run
the command at build time, after the OEO release is unpacked.

## Two things are called `oekg`

- **This app** (`oekg/`, repo root) — reusable OEKG query functionality. Extend
  it when you add new ways to read or write the graph.
- **`factsheet/oekg/`** — an internal package of the `factsheet` app that holds
  the connection setup this app builds on. Not a Django app.

## Related documentation

The main consumer of the OEKG is the **Scenario Bundles** feature. For how the
frontend, Django, OEKG and OEO layers fit together, see the
[Scenario Bundles architecture guide](../docs/oeplatform-code/features/scenario-bundles/architecture.md).
