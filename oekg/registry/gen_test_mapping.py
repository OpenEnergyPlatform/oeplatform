"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

# TEST mapping generator — a stand-in for the (separate-repo) mapping tool, used
# only to produce OBDA for local testing. It reads the registry contract and a
# per-table BINDING (which column maps to which dimension) and emits ontop OBDA
# blocks. NOT the production generator; the binding here is hand-specified
# (normally it comes from the table's oemetadata).
#
# Emits ONLY the mapping blocks (the [PrefixDeclaration]/[MappingDeclaration]
# wrapper already exists in docker/serviceConfigs/ontop/mapping.obda).
#
#   python oekg/registry/gen_test_mapping.py
#
# Conventions matched to the existing eu_leg mapping in that file:
#   * schema "data"; identifiers double-quoted
#   * IRI objects via prefixed CURIEs (oeo:…); literals as plain "{col}"
#   * IAMC tokens via exact-segment array containment (DB untouched)

from __future__ import annotations

from oekg.registry.loader import dimension, load_registry

SCHEMA = "data"
TABLE = "ariadne2_data_with_labels"
PK = "id"
IAMC_COL = "iamc_full_string"
DELIM = " | "

# Per-table binding (would come from oemetadata). column -> dimension key.
# Literal dimensions: the raw cell value becomes the object literal.
LITERAL_COLUMNS = {
    "scenario_year": "scenario_year",
    "value": "quantity_value",
    "unit": "unit",
    "scenario": "scenario",
}
# Computed literals: a SQL expression over EXISTING columns becomes the literal.
#   quantity_kind = the FIRST IAMC segment (the quantity), derived straight from
#   the variable string — IAMC-only, needs NO extra `quantity_variable` column.
#   One value per row → no double-count, no "energy demand as a quantity" artefact.
COMPUTED_LITERALS = {
    "quantity_kind": "split_part(\"iamc_full_string\", ' | ', 1)",
}
# Controlled columns: column -> (dimension key, {db value: object IRI/CURIE}).
CONTROLLED_COLUMNS = {
    "region": ("spatial_region", {"DEU": "llc:Germany"}),
}
# IAMC dimensions still decomposed from the packed string (position-robust tokens).
IAMC_DIMENSIONS = ["sector", "transport_mode", "technology", "qualifier"]


def _slug(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s).strip("_")


def _block(mapping_id: str, target: str, source: str) -> str:
    return (
        f"mappingId       {mapping_id}\n"
        f"target          {target}\n"
        f"source          {source}\n"
    )


def generate() -> str:
    reg = load_registry()
    src = f'SELECT "{PK}" FROM "{SCHEMA}"."{TABLE}"'
    subj = f"oekg:data-descriptor/{TABLE}/{{{PK}}}"
    # NB: ontop's native OBDA parser does NOT allow '#' comment lines inside the
    # [MappingDeclaration] block — emit only mappingId/target/source blocks.
    out = []

    # anchor + table name
    out.append(
        _block(
            f"{TABLE}_TargetClass",
            f'{subj} a oeo:IAO_0000027 ; oeo:OEO_00000504 "{TABLE}"^^xsd:string .',
            src,
        )
    )

    # literal dimensions
    for col, dim_key in LITERAL_COLUMNS.items():
        d = dimension(dim_key, reg)
        out.append(
            _block(
                f"{TABLE}_{dim_key}",
                f'{subj} {d["predicate"]} "{{{col}}}" .',
                f'SELECT "{PK}", "{col}" FROM "{SCHEMA}"."{TABLE}"',
            )
        )

    # computed literals (e.g. quantity_kind = first segment of the variable string)
    for dim_key, expr in COMPUTED_LITERALS.items():
        d = dimension(dim_key, reg)
        out.append(
            _block(
                f"{TABLE}_{dim_key}",
                f'{subj} {d["predicate"]} "{{{dim_key}}}" .',
                f'SELECT "{PK}", {expr} AS {dim_key} FROM "{SCHEMA}"."{TABLE}"',
            )
        )

    # controlled columns: value -> object IRI (WHERE col = value)
    for col, (dim_key, codemap) in CONTROLLED_COLUMNS.items():
        d = dimension(dim_key, reg)
        for code, iri in codemap.items():
            out.append(
                _block(
                    f"{TABLE}_{dim_key}_{_slug(code)}",
                    f'{subj} {d["predicate"]} {iri} .',
                    f'SELECT "{PK}" FROM "{SCHEMA}"."{TABLE}" '
                    f"WHERE \"{col}\" = '{code}'",
                )
            )

    # IAMC token dimensions via array containment (one block per resolved token)
    for dim_key in IAMC_DIMENSIONS:
        d = dimension(dim_key, reg)
        for v in d["values"]:
            if not v["iri"]:
                continue  # unresolved token (e.g. ldv, additional) -> skip
            token = v["code"].replace("'", "''")  # SQL-escape
            # Exact-segment match, parser-friendly: wrap the string in delimiters
            # and LIKE for "| <token> |". Avoids substring collisions (bev vs fcev)
            # and ontop/JSQLParser issues with ANY(string_to_array(...)).
            out.append(
                _block(
                    f"{TABLE}_{dim_key}_{_slug(v['code'])}",
                    f'{subj} {d["predicate"]} {v["iri"]} .',
                    f'SELECT "{PK}" FROM "{SCHEMA}"."{TABLE}" '
                    f"WHERE ('{DELIM}' || \"{IAMC_COL}\" || '{DELIM}') "
                    f"LIKE '%{DELIM}{token}{DELIM}%'",
                )
            )

    return "\n".join(out)


if __name__ == "__main__":
    print(generate())
