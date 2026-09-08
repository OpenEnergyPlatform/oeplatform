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
- `graph_store.py` — the OEKG REST API's own transport to the graph store, and
  `tests/__init__.py`'s `OekgGraphTestCase`, the seam its tests run against. See
  below.

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

### Known gap: only half the pair is pinned

The shape is pinned; the **labels are not**, because the OEO they come from is
not. `podman/Dockerfile` and `docker/docker-entrypoint.dev.sh` both fetch the
ontology from `releases/latest`, and `podman-compose.yaml` mounts a persistent
named volume over `/app/ontologies`, so the release the labels are generated
from can differ between a build and the running container. The command does two
things about it rather than hiding it: it prints the release it used, and it
writes that version into `oeo_labels.ttl`, so a moved ontology shows up as an
`updated` artifact instead of quietly changing what the validator sees. Pass
`--oeo-version` to pin it explicitly. Pinning the ontology fetch itself is a
separate job — it is already duplicated across four sites with three URLs and
inconsistent pinning.

## The API's transport to the graph

`graph_store.py` is a query client and an update client — deliberately **not**
`factsheet/oekg/connection.py`, which the rest of this app still uses.

That module exposes the graph as an rdflib `Graph` over a `SPARQLUpdateStore`
with `autocommit=True`, so every `add()` is its own committed transaction. A
~200-triple bundle costs ~200 requests and 30 s, and an abort halfway leaves
half a bundle in the graph. It also parses the full ontology at import (1.3 GB
resident, ~36 s, per process).

So the boundary sits one step earlier: **keep rdflib for building a graph in
memory, drop it as transport.** Callers assemble triples in an `rdflib.Graph` —
which is also what the validator will read — and `GraphStore` ships them as one
SPARQL request.

```python
store = GraphStore.from_settings()
store.insert(triples)                        # one request
store.update(op_a, op_b)                     # still one request, one transaction
rows = store.select("SELECT ?s WHERE { ?s ?p ?o }")
```

**One request is one transaction, across `;`-separated operations.** That was
established by experiment against Fuseki 5.1.0 on TDB2; it now lives in this
app's tests, so a store upgrade cannot quietly take it away. It is what makes an
update-in-place expressible at all — a delete and an insert in one request
either both apply or neither does.

Two safety properties are built in rather than left to callers:

- **The store's error bodies never escape.** Fuseki answers a bad query with a
  parser dump that echoes the generated query back. It is logged where operators
  can read it, and the raised error carries only a status.
- **`clear()` refuses the default graph.** It exists for tests, and a helper
  that could empty the graph the platform actually uses is one misconfigured
  endpoint away from erasing the knowledge graph.

### Testing against a real store

`OekgGraphTestCase` gives each test its own **named graph**, dropped afterwards,
on a real store. A substitute was considered and rejected: atomicity is a
property of the engine, and an in-memory stand-in would pass whatever we taught
it.

A missing store **skips with a stated reason** rather than failing, so a run
without the compose network is green. Point the tests at a Fuseki of your own
with:

```bash
RDF_DATABASE_HOST=localhost python manage.py test oekg
```

**The availability probe is a write, not a read**, and this is the trap worth
knowing: Fuseki serves queries to anyone but answers updates with `401` unless
the credentials are valid. A probe that only read would call such a store usable
and leave every write test failing instead of skipping. It is also why the CI
service sets `ADMIN_PASSWORD`.

## Two things are called `oekg`

- **This app** (`oekg/`, repo root) — reusable OEKG query functionality. Extend
  it when you add new ways to read or write the graph.
- **`factsheet/oekg/`** — an internal package of the `factsheet` app that holds
  the connection setup this app builds on. Not a Django app.

## Related documentation

The main consumer of the OEKG is the **Scenario Bundles** feature. For how the
frontend, Django, OEKG and OEO layers fit together, see the
[Scenario Bundles architecture guide](../docs/oeplatform-code/features/scenario-bundles/architecture.md).
