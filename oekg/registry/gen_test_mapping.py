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
#   python oekg/registry/gen_test_mapping.py           # ariadne (hand-bound)
#   python oekg/registry/gen_test_mapping.py amiris    # AMIRIS (metadata-driven)
#
# Conventions matched to the existing eu_leg mapping in that file:
#   * schema "data"; identifiers double-quoted
#   * IRI objects via prefixed CURIEs (oeo:…); literals as plain "{col}"
#   * IAMC tokens via exact-segment array containment (DB untouched)
#
# The AMIRIS part is the executable spec of the annotation contract
# (WF-04/05/06/15): it reads each table's SERVED oemetadata from the local OEP,
# classifies isAbout concepts through the registry's facet enums, detects the
# unit shape and the time column from the metadata, derives scenario_year from
# the DECLARED temporal block (never EXTRACT(YEAR)), and reports everything it
# cannot map into oekg/registry/unmapped_columns.json (served with the registry
# contract) — report, don't guess.

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

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


# =============================================================================
# AMIRIS — metadata-driven generation (wide tables -> one data point per CELL)
# =============================================================================
# eu_leg/ariadne are LONG (one `value` column -> subject per row). AMIRIS is
# WIDE (several measure columns per row), so the subject is per (row, column):
#   oekg:data-descriptor/{table}/{column}/{id}
# Each cell-subject carries its own value, constant unit, substance + role
# facets, per-row time_step and the declared-constant scenario_year. Attaching
# several substances to ONE row-subject would conflate the columns (a
# substance-grouped SUM would mix awarded energy with fixed costs) — the
# per-cell subject makes the one-column -> many-triples pattern double-count
# safe by construction.

OEP_META_URL = "http://localhost:8000/api/v0/tables/{table}/meta/"
UNMAPPED_OUT = Path(__file__).with_name("unmapped_columns.json")

AMIRIS_TABLES = [
    "amiris_germany2019_biogas",
    "amiris_germany2019_conventional_plant_operator",
    "amiris_germany2019_conventional_trader",
    "amiris_germany2019_day_ahead_market_single_zone",
    "amiris_germany2019_demand_trader",
    "amiris_germany2019_generic_flexibility_trader",
    "amiris_germany2019_no_support_trader",
    "amiris_germany2019_renewable_trader",
    "amiris_germany2019_sensitivity_forecaster",
    "amiris_germany2019_system_operator_trader",
    "amiris_germany2019_variable_renewable_operator",
]

# Facet dimensions whose enums classify isAbout concepts (WF-04).
FACET_DIMS = ("substance", "transaction_role", "data_role")

# oemetadata @id spellings in the wild: bare local id ("OEO_00140122"), the oeo
# https base, the OLD http+hyphen base, and obo PURLs for UO terms. Normalize
# ALL to the oeo: CURIE (namespace rule / correctness gate 10).
_IRI_BASES = (
    "https://openenergyplatform.org/ontology/oeo/",
    "http://openenergyplatform.org/ontology/oeo/",
    "http://openenergy-platform.org/ontology/oeo/",
    "https://openenergy-platform.org/ontology/oeo/",
    "http://purl.obolibrary.org/obo/",
)


def _norm_curie(at_id: str | None) -> str | None:
    if not at_id:
        return None
    for base in _IRI_BASES:
        if at_id.startswith(base):
            at_id = at_id[len(base) :]
            break
    if re.fullmatch(r"[A-Za-z]+_[0-9]+", at_id):
        return f"oeo:{at_id}"
    return at_id  # unrecognized shape — passed through, will report as unmapped


def _fetch_meta(table: str) -> dict:
    with urllib.request.urlopen(OEP_META_URL.format(table=table)) as fh:
        return json.load(fh)


def _facet_lookup(reg: dict) -> dict[str, tuple[str, str]]:
    """iri (CURIE) -> (facet dimension key, human label)."""
    lut: dict[str, tuple[str, str]] = {}
    for key in FACET_DIMS:
        for v in dimension(key, reg)["values"]:
            if v["iri"]:
                lut[v["iri"]] = (key, v["label"] or v["code"])
    return lut


def _declared_year(resource: dict) -> str | None:
    """WF-06 decision 2: the year is DECLARED per run, never extracted per row.

    Requires temporal.timeseries[0].start and referenceDate to agree on the
    year — a mismatch or a missing declaration yields None (report, don't
    guess; the settlement fencepost row proves EXTRACT(YEAR) wrong).
    """
    tp = resource.get("temporal") or {}
    ts = (tp.get("timeseries") or [{}])[0]
    y_start = (ts.get("start") or "")[:4]
    y_ref = (tp.get("referenceDate") or "")[:4]
    if len(y_start) == 4 and y_start.isdigit() and y_start == y_ref:
        return y_start
    return None


def generate_amiris() -> tuple[str, dict]:
    """Return (obda blocks, unmapped report {table: [{column, reason}]})."""
    reg = load_registry()
    facets = _facet_lookup(reg)
    unit_concept = dimension("unit", reg)["concept"]  # oeo:UO_0000000
    time_dim = dimension("time_step", reg)
    p_value = dimension("quantity_value", reg)["predicate"]
    p_unit = dimension("unit", reg)["predicate"]
    p_year = dimension("scenario_year", reg)["predicate"]
    p_about = reg["generic_super_property"]

    out: list[str] = []
    report: dict[str, list[dict]] = {}

    for table in AMIRIS_TABLES:
        resource = _fetch_meta(table)["resources"][0]
        fields = resource["schema"]["fields"]
        pk = "id"
        notes = report.setdefault(table, [])

        def concepts(f: dict) -> list[str]:
            return [
                c
                for c in (_norm_curie(a.get("@id")) for a in (f.get("isAbout") or []))
                if c
            ]

        # unit shape detection (WF-05): a unit COLUMN wins over field-level
        # units; AMIRIS has none, but the detection is the contract.
        unit_col = next(
            (
                f["name"]
                for f in fields
                if unit_concept in concepts(f) or f["name"] == "unit"
            ),
            None,
        )

        # time column detection (WF-06 decision 3): isAbout -> time concept,
        # fallback: the (single) timestamp-typed column.
        time_col = next(
            (f["name"] for f in fields if time_dim["concept"] in concepts(f)),
            None,
        ) or next((f["name"] for f in fields if f.get("type") == "timestamp"), None)

        year = _declared_year(resource)
        if year is None:
            notes.append(
                {
                    "column": "*",
                    "reason": "no declared temporal.timeseries block — "
                    "yearly axis not emitted (WF-06: never EXTRACT(YEAR))",
                }
            )

        for f in fields:
            col = f["name"]
            if col in (pk, time_col, unit_col):
                continue
            cs = concepts(f)
            classified = [(c, *facets[c]) for c in cs if c in facets]
            unknown = [c for c in cs if c not in facets]
            substances = [c for c, dim_key, _ in classified if dim_key == "substance"]
            roles = [c for c, dim_key, _ in classified if dim_key != "substance"]

            for c in unknown:
                notes.append(
                    {
                        "column": col,
                        "reason": f"concept {c} not in any facet enum — "
                        "not emitted (report, don't guess)",
                    }
                )
            if not substances:
                notes.append(
                    {
                        "column": col,
                        "reason": "no substance concept — column not mapped",
                    }
                )
                continue
            if len(substances) > 1:
                notes.append(
                    {
                        "column": col,
                        "reason": f"conflicting substance concepts {substances} — "
                        "column skipped (single-substance guarantee)",
                    }
                )
                continue
            unit = f.get("unit")
            if not unit or unit == "n/a":
                notes.append(
                    {
                        "column": col,
                        "reason": "substance without resolvable unit — column "
                        "skipped (WF-05: no unit, no comparison)",
                    }
                )
                continue

            subj = f"oekg:data-descriptor/{table}/{col}/{{{pk}}}"
            triples = [
                "a oeo:IAO_0000027",
                f'oeo:OEO_00000504 "{table}"^^xsd:string',
                f'{p_value} "{{{col}}}"',
                f'{p_unit} "{unit}"',
                f"{p_about} {substances[0]}",
            ]
            triples += [f"{p_about} {r}" for r in roles]
            select = [f'"{pk}"', f'"{col}"']
            if time_col:
                dt = time_dim["datatype"]
                triples.append(f'{time_dim["predicate"]} "{{{time_col}}}"^^{dt}')
                select.append(f'"{time_col}"')
            if year is not None:
                triples.append(f'{p_year} "{year}"')
            out.append(
                _block(
                    f"{table}_{col}",
                    f"{subj} {' ; '.join(triples)} .",
                    f'SELECT {", ".join(select)} FROM "{SCHEMA}"."{table}" '
                    f'WHERE "{col}" IS NOT NULL',
                )
            )

    report = {t: n for t, n in report.items() if n}
    return "\n".join(out), report


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "amiris":
        blocks, unmapped = generate_amiris()
        UNMAPPED_OUT.write_text(
            json.dumps(unmapped, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(blocks)
        print(
            f"# unmapped_columns report -> {UNMAPPED_OUT} "
            f"({sum(len(v) for v in unmapped.values())} entries)",
            file=sys.stderr,
        )
    else:
        print(generate())
