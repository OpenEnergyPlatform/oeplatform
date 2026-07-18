#!/usr/bin/env python3
"""Validate the Dimension Property Registry and report its completion state.

Standalone (no Django imports) so it can run in CI or be vendored by the
separate mapping-generator repo. It checks structural integrity and prints
what is still [verify]/[proposed]/TODO — i.e. the Phase-1 work list.

Usage:
    python oekg/registry/validate_registry.py
Exit code 0 if structurally valid (TODOs are warnings, not errors).
Exit code 1 on a structural error (missing keys, dangling value_space ref).
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REGISTRY = Path(__file__).with_name("dimension_property_registry.yaml")


def main() -> int:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    errors: list[str] = []
    todos: list[str] = []

    # --- structural checks -------------------------------------------------
    for key in ("version", "namespaces", "row_anchor", "dimensions", "value_spaces"):
        if key not in data:
            errors.append(f"missing top-level key: {key}")
    if errors:
        _print_errors(errors)
        return 1

    value_spaces = data["value_spaces"]
    seen_keys: set[str] = set()

    for dim in data["dimensions"]:
        key = dim.get("key", "<no key>")
        if key in seen_keys:
            errors.append(f"duplicate dimension key: {key}")
        seen_keys.add(key)

        # every dimension needs a predicate
        pred = dim.get("predicate")
        if not pred:
            errors.append(f"[{key}] has no predicate")
        elif str(pred).startswith("TODO"):
            todos.append(f"[{key}] predicate not yet minted: {pred}")

        # object_kind sanity
        ok = dim.get("object_kind")
        if ok not in ("iri", "literal"):
            errors.append(f"[{key}] object_kind must be 'iri' or 'literal', got {ok!r}")
        if ok == "literal" and not dim.get("datatype"):
            errors.append(f"[{key}] literal dimension needs a datatype")

        # value_space must resolve
        vs = dim.get("value_space")
        if ok == "iri" and not vs:
            errors.append(f"[{key}] iri dimension needs a value_space")
        if vs and vs not in value_spaces:
            errors.append(f"[{key}] dangling value_space reference: {vs}")

        # Token-bound (IAMC) dimensions bind via the token dictionary, and literal
        # dimensions (measures / dataset labels) bind by column, not via an
        # isAbout concept — a null concept is fine for them, not a TODO.
        token_bound = dim.get("value_space") == "iamc_tokens"
        is_literal = dim.get("object_kind") == "literal"
        if dim.get("concept") is None and not token_bound and not is_literal:
            todos.append(f"[{key}] concept (isAbout class) not confirmed")

    # --- concept uniqueness (the join key to oemetadata isAbout) -----------
    # A column's isAbout IRI binds it to the dimension with the matching concept.
    # If two dimensions share a concept, that binding is ambiguous.
    concept_seen: dict[str, str] = {}
    for dim in data["dimensions"]:
        c = dim.get("concept")
        if not c:
            continue
        if c in concept_seen:
            errors.append(
                f"concept {c} shared by [{concept_seen[c]}] and [{dim.get('key')}] "
                f"— must be unique (it is the oemetadata isAbout join key)"
            )
        else:
            concept_seen[c] = dim.get("key")

    # --- value-space IRI completeness (correctness gate 2) -----------------
    for vs_name, mapping in value_spaces.items():
        if not isinstance(mapping, dict):
            continue
        for code, val in mapping.items():
            # YAML may coerce bare keys (NO/YES/ON/OFF -> bool); flag, don't crash
            if not isinstance(code, str):
                errors.append(
                    f"value_space[{vs_name}] has non-string key {code!r} "
                    f'(quote it in YAML, e.g. "NO")'
                )
                continue
            if code.startswith("_"):  # convention/meta keys
                continue
            iri = val.get("iri") if isinstance(val, dict) else val
            if iri is None:
                todos.append(f"value_space[{vs_name}][{code}] has no IRI (@id null)")

    # --- report ------------------------------------------------------------
    if errors:
        _print_errors(errors)
        return 1

    print(
        f"✅ Registry v{data['version']} is structurally valid "
        f"({len(data['dimensions'])} dimensions, {len(value_spaces)} value spaces)."
    )
    if todos:
        print(f"\n⚠️  {len(todos)} item(s) still need attention (Phase-1 work list):")
        for t in todos:
            print(f"   - {t}")
    else:
        print("🎉 No TODOs — registry is fully populated.")
    return 0


def _print_errors(errors: list[str]) -> None:
    print("❌ Registry is INVALID:")
    for e in errors:
        print(f"   - {e}")


if __name__ == "__main__":
    sys.exit(main())
