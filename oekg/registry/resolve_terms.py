#!/usr/bin/env python3
"""Resolve human labels to ontology IRIs via the TIB Terminology Service.

This is the "use the TS instead of hand-maintaining term IRIs" tool. It turns a
label (e.g. "battery electric vehicle") into a canonical OEO IRI by querying
https://api.terminology.tib.eu, preferring an exact label match and flagging
ambiguous results for human confirmation.

Why human-in-the-loop: short codes are ambiguous (e.g. "CO2" returns carbon
dioxide *and* "CO2 price", "CO2 emission", …; "investment" vs "investment cost").
Exact-label matches are auto-confident; everything else is reported, not assumed.

Note on namespaces: OEO imports BFO/IAO/UO/etc. Imported terms keep their obo
IRI (obo/IAO_0000136, obo/UO_0000000) and their imported label; only OEO-native
terms use the oeo: IRI. So results may legitimately mix namespaces. Searching
with ontology=oeo may not surface imported terms -- drop the filter, or use
/api/terms/findByIdAndIsDefiningOntology to get the defining-ontology IRI.

Usage:
    # resolve one or more labels
    python oekg/registry/resolve_terms.py "battery electric vehicle" "energy demand"

    # resolve every still-null token name in the registry's iamc_tokens and
    # print a paste-ready report (does NOT rewrite the commented YAML)
    python oekg/registry/resolve_terms.py --fill-iamc-tokens

Requires network access and the `requests` package.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import quote

API = "https://api.terminology.tib.eu/api/search"
DEFAULT_ONTOLOGY = "oeo"
CANONICAL_PREFIX = "https://openenergyplatform.org/ontology/oeo/"
REGISTRY = Path(__file__).with_name("dimension_property_registry.yaml")


def _get_json(url: str) -> dict:
    import requests  # imported late so --help works without the dep

    resp = requests.get(url, headers={"Accept": "application/json"}, timeout=20)
    resp.raise_for_status()
    return resp.json()


def search(
    label: str,
    ontology: str = DEFAULT_ONTOLOGY,
    want_type: str | None = None,
    rows: int = 10,
) -> list[dict]:
    """Return candidate terms [{iri, label, ontology, type}] for a label.

    NB: do NOT default to type=class — OEO holds some concepts as *individuals*
    (e.g. CRF sectors: "CRF sector (IPCC 2006): domestic aviation"). Omitting the
    type filter returns classes AND individuals. Pass want_type only to narrow.
    """
    url = f"{API}?q={quote(label)}&ontology={quote(ontology)}&rows={rows}"
    if want_type:
        url += f"&type={quote(want_type)}"
    docs = _get_json(url).get("response", {}).get("docs", [])
    return [
        {
            "iri": d.get("iri"),
            "label": d.get("label"),
            "ontology": d.get("ontology_name"),
            "type": d.get("type"),
        }
        for d in docs
    ]


def resolve(label: str, **kw) -> dict:
    """Resolve a label to a single best result with a confidence verdict.

    Returns {label, iri, match, candidates} where match is one of:
      'exact'     — exactly one case-insensitive label match (auto-confident)
      'ambiguous' — several candidates / no exact label match (confirm manually)
      'none'      — nothing came back
    """
    cands = search(label, **kw)
    if not cands:
        return {"label": label, "iri": None, "match": "none", "candidates": []}
    want = label.strip().lower()
    exact = [c for c in cands if (c["label"] or "").strip().lower() == want]
    if len(exact) == 1:
        return {
            "label": label,
            "iri": exact[0]["iri"],
            "match": "exact",
            "candidates": cands,
        }
    return {"label": label, "iri": None, "match": "ambiguous", "candidates": cands}


def _short(iri: str | None) -> str:
    if not iri:
        return "null"
    if iri.startswith(CANONICAL_PREFIX):
        return "oeo:" + iri[len(CANONICAL_PREFIX) :]
    return iri


def _report(results: list[dict]) -> int:
    unresolved = 0
    for r in results:
        if r["match"] == "exact":
            print(f"  ✅ {r['label']!r:45} -> {_short(r['iri'])}")
        else:
            unresolved += 1
            tag = "❓ ambiguous" if r["match"] == "ambiguous" else "∅ not found"
            print(f"  {tag}: {r['label']!r}")
            for c in r["candidates"][:5]:
                print(f"       - {_short(c['iri'])}  ({c['label']})")
    print(
        f"\n{len(results) - unresolved}/{len(results)} auto-resolved; "
        f"{unresolved} need manual confirmation."
    )
    return unresolved


def fill_iamc_tokens() -> int:
    import yaml

    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    tokens = data["value_spaces"]["iamc_tokens"]
    todo = {
        k: v for k, v in tokens.items() if isinstance(v, dict) and v.get("iri") is None
    }
    if not todo:
        print("All iamc_tokens already have IRIs. 🎉")
        return 0
    print(f"Resolving {len(todo)} unresolved token name(s) against the TS…\n")
    results = [resolve(v["name"]) for v in todo.values()]
    rc = _report(results)
    print(
        "\nPaste the ✅ lines into dimension_property_registry.yaml "
        "(iamc_tokens), tag them [ts]. Confirm the ❓ ones first."
    )
    return rc


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("labels", nargs="*", help="labels to resolve")
    ap.add_argument("--ontology", default=DEFAULT_ONTOLOGY)
    ap.add_argument("--type", default="class", dest="want_type")
    ap.add_argument(
        "--fill-iamc-tokens",
        action="store_true",
        help="resolve every null token name in the registry",
    )
    args = ap.parse_args(argv)

    if args.fill_iamc_tokens:
        return 1 if fill_iamc_tokens() else 0
    if not args.labels:
        ap.print_help()
        return 0
    results = [
        resolve(lbl, ontology=args.ontology, want_type=args.want_type)
        for lbl in args.labels
    ]
    return 1 if _report(results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
