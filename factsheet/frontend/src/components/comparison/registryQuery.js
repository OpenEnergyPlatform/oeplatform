// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// P1/P2 of the registry-driven refactor (see Obsidian "10 - Frontend Refactor
// Plan"). Pure helpers — no React — that build SPARQL from the Dimension
// Property Registry contract served by GET /oekg/registry/. Unit-testable.
//
// Contract shape (oekg/registry/loader.py):
//   { namespaces, row_anchor, generic_super_property, dimensions: [
//       { key, concept, predicate, object_kind, datatype, value_space,
//         values: [{ code, iri, label }] } ] }
//
// KEY IDEA — disambiguating shared predicates:
//   IAMC dimensions currently share the generic `is about` predicate
//   (oeo:IAO_0000136). Selecting `?s <pred> ?technology` alone would bind to
//   EVERY annotated concept on the row. Because the token dictionary assigns
//   each value to exactly one dimension, we isolate a dimension by constraining
//   its variable to that dimension's enum IRIs:
//       ?s oeo:IAO_0000136 ?technology .
//       FILTER(?technology IN ( <…technology IRIs…> ))
//   This needs the token IRIs filled (resolve_terms.py) but NO new predicates.

const TABLE_PRED = "oeo:OEO_00000504"; // table-name predicate (row anchor)
const VALUE_KEY = "quantity_value"; // dimension carrying the numeric measure

export function prefixHeader(registry) {
  return Object.entries(registry.namespaces || {})
    .map(([p, iri]) => `PREFIX ${p}: <${iri}>`)
    .join("\n");
}

export function expandCurie(registry, curie) {
  if (!curie || curie.startsWith("http") || !curie.includes(":")) return curie;
  const i = curie.indexOf(":");
  const prefix = curie.slice(0, i);
  const local = curie.slice(i + 1);
  const base = (registry.namespaces || {})[prefix];
  return base ? `${base}${local}` : curie;
}

// Full http IRI -> <...>; CURIE (prefix declared in the header) -> verbatim.
export function sparqlTerm(iriOrCurie) {
  if (!iriOrCurie) return iriOrCurie;
  return iriOrCurie.startsWith("http") ? `<${iriOrCurie}>` : iriOrCurie;
}

// Predicates used by >1 iri-dimension (i.e. the generic `is about`) — these
// need enum isolation.
export function sharedPredicates(registry) {
  const counts = {};
  for (const d of registry.dimensions || []) {
    if (d.object_kind !== "iri") continue;
    counts[d.predicate] = (counts[d.predicate] || 0) + 1;
  }
  return new Set(Object.keys(counts).filter((p) => counts[p] > 1));
}

const enumTerms = (dim) =>
  (dim.values || []).filter((v) => v.iri).map((v) => sparqlTerm(v.iri));

const tableFilter = (tables) =>
  tables && tables.length
    ? `FILTER(?table_name IN (${tables.map((t) => `"${t}"`).join(", ")})) .`
    : "";

// Distinct values of one dimension actually present in the selected tables.
export function dimensionValuesQuery({ registry, dim, tables = [] }) {
  let isolate = "";
  if (dim.object_kind === "iri" && sharedPredicates(registry).has(dim.predicate)) {
    const set = enumTerms(dim);
    if (set.length) isolate = `FILTER(?v IN (${set.join(", ")})) .`;
  }
  return `${prefixHeader(registry)}
SELECT DISTINCT ?v ?table_name WHERE {
  ?s ${dim.predicate} ?v . ?s ${TABLE_PRED} ?table_name .
  ${isolate}
  ${tableFilter(tables)}
}`;
}

// Units present in a table, most common first. If `dim` is given, only units
// that CO-OCCUR with that dimension are returned (e.g. units that actually apply
// when breaking down by technology) — keeps the unit list relevant + small.
export function unitFrequencyQuery({ registry, table, dim }) {
  const unitDim = (registry.dimensions || []).find((d) => d.key === "unit");
  const pred = unitDim ? unitDim.predicate : "oeo:OEO_00040010";
  let cond = "";
  if (dim && dim.key !== "unit") {
    let iso = "";
    if (dim.object_kind === "iri" && sharedPredicates(registry).has(dim.predicate)) {
      const set = enumTerms(dim);
      if (set.length) iso = ` FILTER(?dv IN (${set.join(", ")}))`;
    }
    cond = ` ?s ${dim.predicate} ?dv .${iso}`;
  }
  return `${prefixHeader(registry)}
SELECT ?v (COUNT(?s) AS ?c) WHERE {
  ?s ${TABLE_PRED} ?t . FILTER(?t = "${table}") ?s ${pred} ?v .${cond}
} GROUP BY ?v ORDER BY DESC(?c)`;
}

// Distinct values of a dimension by frequency (most common first), optionally
// scoped by another (literal) dimension = value — e.g. quantities in a table, or
// the units that occur FOR a chosen quantity (unit follows the quantity).
export function valueFrequencyQuery({ registry, table, dim, scopeDim, scopeValue }) {
  let scope = "";
  if (scopeDim && scopeValue) {
    const esc = String(scopeValue).replace(/"/g, '\\"');
    scope = ` ?s ${scopeDim.predicate} ?sv . FILTER(STR(?sv) = "${esc}")`;
  }
  return `${prefixHeader(registry)}
SELECT ?v (COUNT(?s) AS ?c) WHERE {
  ?s ${TABLE_PRED} ?t . FILTER(?t = "${table}") ?s ${dim.predicate} ?v .${scope}
} GROUP BY ?v ORDER BY DESC(?c)`;
}

// Cheap existence check: does this table populate this dimension at all?
// Used to show only dimensions/presets that will actually return data.
export function dimensionAskQuery({ registry, table, dim }) {
  let iso = "";
  if (dim.object_kind === "iri" && sharedPredicates(registry).has(dim.predicate)) {
    const set = enumTerms(dim);
    if (set.length) iso = ` FILTER(?v IN (${set.join(", ")}))`;
  }
  return `${prefixHeader(registry)}
ASK { ?s ${TABLE_PRED} ?t . FILTER(?t = "${table}") ?s ${dim.predicate} ?v .${iso} }`;
}

// The comparison query: select the numeric value + the chosen dimension axes,
// filtered by the user's selections.
//   dims:    array of dimension keys to project (e.g. ["technology","scenario_year"])
//   filters: { [dimKey]: code[] } user selections
export function buildComparisonQuery({ registry, tables = [], filters = {}, dims = [] }) {
  const shared = sharedPredicates(registry);
  const byKey = Object.fromEntries((registry.dimensions || []).map((d) => [d.key, d]));
  const selected = dims.map((k) => byKey[k]).filter(Boolean);

  const valueDim = byKey[VALUE_KEY];
  const patterns = [
    `?s ${valueDim ? valueDim.predicate : "oeo:OEO_00140178"} ?value .`,
    `?s ${TABLE_PRED} ?table_name .`,
  ];
  const vars = [];
  const filterLines = [];

  const tf = tableFilter(tables);
  if (tf) filterLines.push(tf);

  for (const d of selected) {
    if (d.key === VALUE_KEY) continue;
    const v = `?${d.key}`;
    vars.push(v);
    patterns.push(`?s ${d.predicate} ${v} .`);

    // isolate shared-predicate (generic is-about) dims by their enum set
    if (d.object_kind === "iri" && shared.has(d.predicate)) {
      const set = enumTerms(d);
      if (set.length) patterns.push(`FILTER(${v} IN (${set.join(", ")})) .`);
    }

    const codes = filters[d.key];
    if (codes && codes.length) {
      const terms = codes.map((code) => {
        if (d.object_kind === "iri") {
          const val = (d.values || []).find((x) => x.code === code);
          return sparqlTerm(val ? val.iri : code);
        }
        return `"${code}"`;
      });
      filterLines.push(`FILTER(${v} IN (${terms.join(", ")})) .`);
    }
  }

  return `${prefixHeader(registry)}
SELECT DISTINCT ?s ?value ?table_name ${vars.join(" ")} WHERE {
  ${patterns.join("\n  ")}
  ${filterLines.join("\n  ")}
}`;
}

// Map a result's full IRI back to a human label for a given dimension.
export function labelForIri(registry, dim, fullIri) {
  for (const v of dim.values || []) {
    if (v.iri && expandCurie(registry, v.iri) === fullIri) return v.label || v.code;
  }
  return fullIri;
}