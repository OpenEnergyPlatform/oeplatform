"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

# Load the Dimension Property Registry and project it to the `registry.json`
# CONTRACT. This is the single API for consuming the registry. Used by:
#   * the OEP Django app  -> serves the contract as registry.json to the frontend
#     (oekg/views.py: dimension_registry_view).
#   * Philipp's mapping generator (imported by OEP as a Python package) -> OEP
#     calls the generator entrypoint with this contract dict. The generator never
#     imports OEP internals; it just accepts the dict.
#
# The contract is the ONE shared shape (frontend + generator + any external tool):
#   {
#     "version", "namespaces", "row_anchor", "generic_super_property",
#     "dimensions": [
#       {"key", "concept", "predicate", "object_kind", "datatype",
#        "value_space", "values": [{"code", "iri", "label"}]}
#     ]
#   }
# Value spaces are inlined per dimension as `values` (resolved code -> IRI + label)
# so both the frontend (build filters) and the generator (emit one block per value)
# read the same place. iamc_tokens are filtered to the dimension they belong to.

from __future__ import annotations

import json
from pathlib import Path

import yaml

REGISTRY_PATH = Path(__file__).with_name("dimension_property_registry.yaml")


def _load_yaml(path: Path = REGISTRY_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _normalize_values(value_space: dict, dimension_key: str) -> list[dict]:
    """Return [{code, iri, label}] for one dimension's value space.

    Handles both shapes: flat ``code -> iri`` (gas/scenario/region) and
    structured ``code -> {iri, dimension, name}`` (iamc_tokens). For the
    structured shape, only values whose ``dimension`` matches are returned.
    """
    out: list[dict] = []
    if not isinstance(value_space, dict):
        return out
    for code, val in value_space.items():
        # skip non-string keys (YAML may coerce e.g. bare NO) and meta keys
        if not isinstance(code, str) or code.startswith("_"):
            continue
        if isinstance(val, dict):
            if val.get("dimension") and val.get("dimension") != dimension_key:
                continue
            out.append({"code": code, "iri": val.get("iri"), "label": val.get("name")})
        else:
            out.append({"code": code, "iri": val, "label": None})
    return out


def build_contract(raw: dict | None = None) -> dict:
    """Project the raw registry YAML into the shared registry.json contract."""
    raw = raw if raw is not None else _load_yaml()
    value_spaces = raw.get("value_spaces", {})
    dimensions = []
    for d in raw.get("dimensions", []):
        vs_name = d.get("value_space")
        values = (
            _normalize_values(value_spaces.get(vs_name, {}), d["key"])
            if vs_name
            else []
        )
        dimensions.append(
            {
                "key": d["key"],
                "concept": d.get("concept"),
                "predicate": d["predicate"],
                "object_kind": d["object_kind"],
                "datatype": d.get("datatype"),
                "value_space": vs_name,
                "values": values,
            }
        )
    return {
        "version": raw.get("version"),
        "namespaces": raw.get("namespaces", {}),
        "row_anchor": raw.get("row_anchor", {}),
        "generic_super_property": raw.get("generic_super_property"),
        "dimensions": dimensions,
    }


def load_registry() -> dict:
    """The contract dict served by the Django view + consumed by the generator.

    Reads the YAML fresh each call so registry edits appear without a restart
    (the file is tiny; this endpoint is low-traffic).
    """
    return build_contract()


# --- convenience accessors (handy for the generator) -------------------------
def dimension(key: str, contract: dict | None = None) -> dict | None:
    contract = contract or load_registry()
    return next((d for d in contract["dimensions"] if d["key"] == key), None)


def predicate_for(key: str, contract: dict | None = None) -> str | None:
    d = dimension(key, contract)
    return d["predicate"] if d else None


def dimension_for_concept(concept: str, contract: dict | None = None) -> dict | None:
    """Find the dimension whose ``concept`` (isAbout class IRI) matches.

    This is the JOIN KEY the generator uses to bind a table column (its
    oemetadata ``isAbout``) to a registry dimension, and thus its predicate.
    Returns None if unmapped; raises if >1 dimension claims the concept
    (concepts must be unique — see validate_registry.py).

    NB: a generic concept shared across IAMC dimensions (e.g. "variable") is NOT
    bound this way — those columns decompose via the token dictionary instead.
    """
    contract = contract or load_registry()
    hits = [d for d in contract["dimensions"] if d.get("concept") == concept]
    if len(hits) > 1:
        raise ValueError(
            f"ambiguous concept {concept!r}: claimed by {[d['key'] for d in hits]}"
        )
    return hits[0] if hits else None


def expand(curie: str, contract: dict | None = None) -> str:
    """Expand a ``prefix:Local`` CURIE to a full IRI using the registry prefixes."""
    contract = contract or load_registry()
    if ":" not in curie:
        return curie
    prefix, local = curie.split(":", 1)
    base = contract["namespaces"].get(prefix)
    return f"{base}{local}" if base else curie


if __name__ == "__main__":
    print(json.dumps(build_contract(), indent=2, ensure_ascii=False))
