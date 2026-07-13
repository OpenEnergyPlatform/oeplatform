// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// PROTOTYPE (wayfinder WF-07) — throwaway data plumbing for the multi-source
// selection variants. SPARQL builders + fetchers shared by all variants.
// The decided semantics live in ../comparability.js (keep); this file dies
// with the prototype.

import axios from "axios";
import conf from "../../../conf.json";
import CSRFToken from "../../csrfToken.js";
import {
  prefixHeader,
  sparqlTerm,
  sharedPredicates,
} from "../registryQuery.js";

export const TABLE_PRED = "oeo:OEO_00000504";
export const ROWS_SCHEMA = "model_draft";

export async function postSparql(query) {
  const res = await axios.post(conf.obdi, query, {
    headers: {
      "X-CSRFToken": CSRFToken(),
      Accept: "application/sparql-results+json",
      "Content-Type": "application/sparql-query",
    },
  });
  return res.data;
}

const bindings = (d) => d?.results?.bindings || [];

// ---- catalog ---------------------------------------------------------------

// All tables present in the VKG — the card list is grounded in the semantic
// layer (mapped tables only), not in a hand-kept list.
export async function fetchMappedTables(registry) {
  const q = `${prefixHeader(registry)}
SELECT DISTINCT ?t WHERE { ?s ${TABLE_PRED} ?t } ORDER BY ?t`;
  return bindings(await postSparql(q)).map((b) => b.t.value);
}

// oemetadata for one table (title/description/keywords for the rich cards).
export async function fetchTableMeta(table) {
  try {
    const res = await axios.get(
      `/api/v0/schema/${ROWS_SCHEMA}/tables/${table}/meta/`
    );
    const d = res.data || {};
    const r = (d.resources || [])[0] || {};
    return {
      title: r.title || d.title || table,
      description: r.description || d.description || "",
      keywords: r.keywords || d.keywords || [],
      subject: (r.subject || d.subject || [])
        .map((s) => s?.name)
        .filter(Boolean),
    };
  } catch (e) {
    return { title: table, description: "", keywords: [], subject: [] };
  }
}

// PROTOTYPE heuristic: dataset family for grouping cards. Should come from the
// Datasets feature (semantic layer) eventually — flagged for the maintainer.
export function familyOf(table) {
  if (table.startsWith("amiris_")) return "AMIRIS Germany 2019";
  if (table.startsWith("ariadne")) return "Ariadne (IAMC)";
  if (table.startsWith("eu_leg")) return "EU emission reporting (SIROP)";
  return "Other";
}

// ---- per-table facts (feed the verdict) ------------------------------------

// Which tables populate a literal dimension at all (one query for ALL tables:
// cheaper than per-table ASKs for catalog-wide facts like time_step).
export async function tablesWithDimension(registry, dim) {
  const q = `${prefixHeader(registry)}
SELECT DISTINCT ?t WHERE { ?s ${TABLE_PRED} ?t . ?s ${dim.predicate} ?v }`;
  return new Set(bindings(await postSparql(q)).map((b) => b.t.value));
}

// Distinct values of a measure dimension per table, across the whole VKG.
// Enum isolation for the shared is-about predicate (substance).
export async function measuresByTable(registry, dim) {
  let iso = "";
  if (
    dim.object_kind === "iri" &&
    sharedPredicates(registry).has(dim.predicate)
  ) {
    const set = (dim.values || [])
      .filter((v) => v.iri)
      .map((v) => sparqlTerm(v.iri));
    if (set.length) iso = `FILTER(?v IN (${set.join(", ")})) .`;
  }
  const q = `${prefixHeader(registry)}
SELECT DISTINCT ?t ?v WHERE { ?s ${TABLE_PRED} ?t . ?s ${dim.predicate} ?v . ${iso} }`;
  const out = {};
  for (const b of bindings(await postSparql(q))) {
    (out[b.t.value] = out[b.t.value] || []).push(b.v.value);
  }
  return out;
}

// Units present per table FOR one chosen measure (unit follows the measure;
// the unit filter spans all selected sources — WF-02).
export async function unitsByTableForMeasure({ registry, tables, measure }) {
  const unitDim = (registry.dimensions || []).find((d) => d.key === "unit");
  const scope = measureScope(registry, measure);
  const q = `${prefixHeader(registry)}
SELECT ?t ?v (COUNT(?s) AS ?c) WHERE {
  ?s ${TABLE_PRED} ?t . FILTER(?t IN (${tables.map((t) => `"${t}"`).join(", ")}))
  ?s ${unitDim.predicate} ?v . ${scope}
} GROUP BY ?t ?v ORDER BY DESC(?c)`;
  const out = {};
  for (const b of bindings(await postSparql(q))) {
    (out[b.t.value] = out[b.t.value] || []).push(b.v.value);
  }
  return out;
}

// dimension availability per table (the WF-07 "union of per-table ASKs")
export async function askDimension(registry, table, dim) {
  let iso = "";
  if (
    dim.object_kind === "iri" &&
    sharedPredicates(registry).has(dim.predicate)
  ) {
    const set = (dim.values || [])
      .filter((v) => v.iri)
      .map((v) => sparqlTerm(v.iri));
    if (set.length) iso = ` FILTER(?v IN (${set.join(", ")}))`;
  }
  const q = `${prefixHeader(registry)}
ASK { ?s ${TABLE_PRED} ?t . FILTER(?t = "${table}") ?s ${dim.predicate} ?v .${iso} }`;
  try {
    return !!(await postSparql(q)).boolean;
  } catch (e) {
    return true; // fail open, like the existing view
  }
}

// ---- the merged, aggregated comparison query -------------------------------

function measureScope(registry, measure) {
  if (!measure || measure.space === "none") return "";
  const byKey = Object.fromEntries(
    (registry.dimensions || []).map((d) => [d.key, d])
  );
  if (measure.space === "substance") {
    const dim = byKey.substance;
    return `?s ${dim.predicate} ?measure . FILTER(?measure = ${sparqlTerm(measure.value)}) .`;
  }
  const dim = byKey.quantity_kind;
  const esc = String(measure.value).replace(/"/g, '\\"');
  return `?s ${dim.predicate} ?measure . FILTER(STR(?measure) = "${esc}") .`;
}

// Time-bucket patterns per WF-06/WF-08:
//  * year   → the DECLARED ?scenario_year constant, never EXTRACT(YEAR) — the
//             AMIRIS December settlement lands on the 2020-01-01 fencepost.
//  * hour   → the raw ?time_step (one row per hour).
//  * day/month → BIND(...) on ?time_step; ontop rejects expressions inside
//             GROUP BY, so every bucket part gets its own BIND (WF-08 gotcha).
//  * week   → not buildable in SPARQL (no WEEK()); disabled in the UI.
const BUCKETS = {
  year: {
    patterns: (yDim) => [`?s ${yDim.predicate} ?bucket_y .`],
    vars: ["?bucket_y"],
  },
  month: {
    patterns: (yDim, tsDim) => [
      `?s ${tsDim.predicate} ?ts .`,
      `BIND(YEAR(?ts) AS ?bucket_y) BIND(MONTH(?ts) AS ?bucket_m)`,
    ],
    vars: ["?bucket_y", "?bucket_m"],
  },
  day: {
    patterns: (yDim, tsDim) => [
      `?s ${tsDim.predicate} ?ts .`,
      `BIND(YEAR(?ts) AS ?bucket_y) BIND(MONTH(?ts) AS ?bucket_m) BIND(DAY(?ts) AS ?bucket_d)`,
    ],
    vars: ["?bucket_y", "?bucket_m", "?bucket_d"],
  },
  hour: {
    patterns: (yDim, tsDim) => [`?s ${tsDim.predicate} ?bucket_ts .`],
    vars: ["?bucket_ts"],
  },
};

export function bucketLabel(row, granularity) {
  const p2 = (v) => String(v).padStart(2, "0");
  const g = (k) => row[k]?.value;
  if (granularity === "year") return g("bucket_y");
  if (granularity === "month") return `${g("bucket_y")}-${p2(g("bucket_m"))}`;
  if (granularity === "day")
    return `${g("bucket_y")}-${p2(g("bucket_m"))}-${p2(g("bucket_d"))}`;
  return (g("bucket_ts") || "").replace("T", " ").slice(0, 16);
}

// One merged query across all selected tables: GROUP BY (bucket, source,
// group-dim), aggregation function from the registry hint — the chart never
// chooses it (WF-06). xsd:double cast: quantity_value is a plain literal.
export function buildMergedQuery({
  registry,
  tables,
  measure,
  unit,
  granularity,
  groupKey,
  agg,
}) {
  const byKey = Object.fromEntries(
    (registry.dimensions || []).map((d) => [d.key, d])
  );
  const valueDim = byKey.quantity_value;
  const unitDim = byKey.unit;
  const bucket = BUCKETS[granularity] || BUCKETS.year;

  const patterns = [
    `?s ${valueDim.predicate} ?raw_value .`,
    `?s ${TABLE_PRED} ?table_name .`,
    `FILTER(?table_name IN (${tables.map((t) => `"${t}"`).join(", ")})) .`,
    measureScope(registry, measure),
    ...bucket.patterns(byKey.scenario_year, byKey.time_step),
  ];
  if (unit) {
    patterns.push(
      `?s ${unitDim.predicate} ?unit . FILTER(STR(?unit) = "${unit.replace(/"/g, '\\"')}") .`
    );
  }
  const groupVars = ["?table_name", ...bucket.vars];
  if (groupKey && groupKey !== "source") {
    const gd = byKey[groupKey];
    if (gd) {
      patterns.push(`?s ${gd.predicate} ?${gd.key} .`);
      if (
        gd.object_kind === "iri" &&
        sharedPredicates(registry).has(gd.predicate)
      ) {
        const set = (gd.values || [])
          .filter((v) => v.iri)
          .map((v) => sparqlTerm(v.iri));
        if (set.length)
          patterns.push(`FILTER(?${gd.key} IN (${set.join(", ")})) .`);
      }
      groupVars.push(`?${gd.key}`);
    }
  }
  const fn = (agg || "sum").toLowerCase() === "mean" ? "AVG" : "SUM";
  return `${prefixHeader(registry)}
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ${groupVars.join(" ")} (${fn}(xsd:double(?raw_value)) AS ?value) WHERE {
  ${patterns.filter(Boolean).join("\n  ")}
} GROUP BY ${groupVars.join(" ")}`;
}
