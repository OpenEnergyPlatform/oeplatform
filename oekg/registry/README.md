# Dimension Property Registry

The **single source of truth** for the harmonized RDF vocabulary used by the
scenario comparison service. It maps each comparable _dimension_ (region, gas,
scenario type, technology, …) to the **predicate** used in generated triples,
the **object kind** (IRI vs literal), and — for controlled vocabularies — the
**value space** (`code → IRI`).

## Why it exists

- oemetadata `isAbout` only gives a **concept (a class)**; an RDF triple needs a
  **predicate (an object property)**. The Terminology Service can't derive that
  link yet, so it must live as data.
- The mapping generator (separate repo) currently **hardcodes** this
  `concept → predicate` lookup.
- The comparison UI
  (`factsheet/frontend/src/components/comparison/quantitativeView.jsx`)
  **hardcodes** the same predicates on the query side.

This file replaces _both_ hardcodings. Harmonization only works if every
dataset's mapping and the UI use the **same** predicates and value IRIs — that
is exactly what this registry guarantees.

## Files

| File                               | Purpose                                                                                                                                                                                     |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dimension_property_registry.yaml` | The registry itself (source of truth). Provenance-tagged: `[confirmed]` / `[verify]` / `[ts]`.                                                                                              |
| `loader.py`                        | Loads the YAML → the `registry.json` **contract dict** (`load_registry()`), inlines value spaces per dimension, + accessors (`predicate_for`, `expand`). The shared API for both consumers. |
| `validate_registry.py`             | Structural validator + Phase-1 work-list report. No Django deps; CI-ready.                                                                                                                  |
| `resolve_terms.py`                 | Resolves labels → IRIs via the TIB Terminology Service (so term IRIs aren't hand-maintained).                                                                                               |

## Consumers (one shared contract)

The registry is an **input**, not a generator output. `loader.build_contract()`
produces one dict consumed by both:

- **Frontend** ← `GET /oekg/registry/`
  (`oekg/views.py: dimension_registry_view`) → builds dynamic SPARQL + filter
  UI.
- **Mapping generator** (imported by OEP as a Python package) ← OEP calls
  `generate(table_oemetadata: dict, registry: dict) -> obda_str` with this same
  dict in-process; the generator never imports OEP internals.

```bash
python oekg/registry/loader.py        # print the registry.json contract
```

## Curated here vs resolved from the TS

The registry is **only** the `dimension → predicate` map (+
object_kind/datatype) — a modelling choice the Terminology Service cannot derive
(property-by-label search is unreliable). All **term IRIs** (the `value_spaces`)
are resolvable from the TS and should be treated as a re-runnable cache, not
authored truth:

```bash
python oekg/registry/resolve_terms.py "battery electric vehicle"
python oekg/registry/resolve_terms.py --fill-iamc-tokens
```

Per-dataset `value → IRI` mappings ultimately belong in oemetadata
`valueReference`, filled by the resolver and human-confirmed where ambiguous
(codes like `CO2` return several candidates). See the Obsidian note _08 -
Terminology Service_.

## Usage

```bash
python oekg/registry/validate_registry.py
```

Exit code `0` = structurally valid (TODOs are warnings); `1` = structural error.

## Consumers

- **Mapping generator (separate repo):**
  `property_url = registry.predicate_for(concept_or_dimension)`, then
  `f'{subject_url} {property_url} <{object_iri}> .'`. Vendor or fetch this file.
- **Comparison UI:** should read predicates from here instead of hardcoding them
  (Phase 2).

## Conventions

- Specific predicates should be declared `rdfs:subPropertyOf` the
  `generic_super_property` (`obo:IAO_0000136`, "is about"), so a generic query
  catches everything and typed queries still enable dimensional grouping.
- **Namespace hygiene (correctness gate 10):** one canonical IRI form for
  `oeo:`/`oekg:` must be used for _every_ predicate and object. See the warning
  at the top of the YAML — the existing `.obda` files mix
  `http://openenergy-platform.org/…` and `https://openenergyplatform.org/…`.

## Background docs

- `scripts/oevkg/sem_mapping/ANNOTATION_AND_MAPPING_DESIGN.md` (§5)
- Obsidian vault: _04 - Annotation Contract_, _05 - Generator Correctness_,
  _07 - Concept to Predicate_
