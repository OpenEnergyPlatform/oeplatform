// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// The comparability contract (wayfinder WF-12, amended by WF-13): a pure,
// unit-testable verdict over DECLARED facts only — registry contract +
// SPARQL-discovered facts per table. No chart heuristics.
//
// A *series* is one (table, measure, unit, granularity) tuple:
//   { table, space, measure, measureLabel?, unit, granularity, aggregation }
//   space:        measure space — "substance" (IRI values) | "quantity_kind"
//                 (IAMC literal values). Spaces NEVER cross (WF-12 decision 1).
//   unit:         literal unit string (WF-05); equality is the merge guard.
//   granularity:  native temporal granularity on the WF-06 ladder, or null
//                 when the table declares no temporal anchor.
//   aggregation:  "sum" | "mean" | null — the registry's per-substance hint
//                 (WF-06); null means re-scaling this series is NOT declared
//                 valid and coarser rungs are unreachable (report-don't-guess).
//
// Verdicts: merge | aggregate_first | blocked(reason), reasons drawn from the
// fixed WF-12 vocabulary (+ "incommensurable" added by WF-13).

export const LADDER = ["hour", "day", "week", "month", "year"];

// Which coarser rungs a native granularity can be aggregated onto. Weeks cross
// month and year boundaries (ISO), so "week" reaches nothing and nothing on the
// calendar chain reaches "week" from month upward.
const REACHABLE = {
  hour: ["hour", "day", "week", "month", "year"],
  day: ["day", "week", "month", "year"],
  week: ["week"],
  month: ["month", "year"],
  year: ["year"],
};

export const REASONS = {
  SPACES: "measure spaces not aligned",
  MEASURE: "measure mismatch",
  UNIT: "unit mismatch",
  INCOMMENSURABLE: "incommensurable",
  GRANULARITY: "granularity unreachable",
  MISSING_UNIT: "missing declaration (unit)",
  MISSING_TEMPORAL: "missing declaration (temporal)",
  MISSING_AGGREGATION: "missing declaration (aggregation validity)",
};

const blocked = (reason, detail) => ({ kind: "blocked", reason, detail });

// The rungs a series may be displayed at: its native rung plus — only when the
// registry declares aggregation validity — every reachable coarser rung.
export function reachableLevels(series) {
  if (!series.granularity) return [];
  const levels = REACHABLE[series.granularity] || [];
  return series.aggregation ? levels : [series.granularity];
}

// WF-13 seam — unit leg beyond string equality. `units` is the (future)
// registry-served map keyed by literal unit string:
//   { [unitString]: { iri, quantity_kind, si_factor?, si_offset? } }
// Same quantity kind + both SI factors present => convertible (auto-convert +
// chart annotation). Differing quantity kinds => incommensurable (kt CO2e vs
// kt is a quantity-kind mismatch, not a factor away). Unknown strings keep
// today's blocked(unit mismatch). The registry does not serve `units:` yet,
// so with units == null string equality is the whole leg (WF-12 / WF-05).
function unitLeg(a, b, units) {
  if (!a.unit || !b.unit) {
    const missing = [a, b].filter((s) => !s.unit).map((s) => s.table);
    return blocked(
      REASONS.MISSING_UNIT,
      `${missing.join(", ")} declares no unit for this measure`
    );
  }
  if (a.unit === b.unit) return { ok: true };
  const ua = units && units[a.unit];
  const ub = units && units[b.unit];
  if (ua && ub) {
    if (ua.quantity_kind !== ub.quantity_kind) {
      return blocked(
        REASONS.INCOMMENSURABLE,
        `${a.unit} (${ua.quantity_kind}) and ${b.unit} (${ub.quantity_kind}) measure different quantity kinds`
      );
    }
    if (ua.si_factor != null && ub.si_factor != null) {
      return {
        ok: true,
        conversion: {
          from: b.unit,
          to: a.unit,
          factor: ub.si_factor / ua.si_factor,
        },
      };
    }
  }
  return blocked(
    REASONS.UNIT,
    `${a.table} reports ${a.unit} · ${b.table} reports ${b.unit}`
  );
}

// The WF-12 pairwise predicate.
export function compareSeries(a, b, { units = null } = {}) {
  if (a.space !== b.space) {
    return blocked(
      REASONS.SPACES,
      `${a.table} annotates ${a.space} · ${b.table} annotates ${b.space}`
    );
  }
  if (a.measure !== b.measure) {
    return blocked(
      REASONS.MEASURE,
      `${a.table} measures ${a.measureLabel || a.measure} · ${b.table} measures ${b.measureLabel || b.measure}`
    );
  }
  const u = unitLeg(a, b, units);
  if (u.kind === "blocked") return u;
  if (!a.granularity || !b.granularity) {
    const missing = [a, b].filter((s) => !s.granularity).map((s) => s.table);
    return blocked(
      REASONS.MISSING_TEMPORAL,
      `${missing.join(", ")} declares no temporal granularity`
    );
  }
  if (a.granularity === b.granularity) {
    return { kind: "merge", target: a.granularity, conversion: u.conversion };
  }
  const common = reachableLevels(a).filter((l) =>
    reachableLevels(b).includes(l)
  );
  if (!common.length) {
    const noAgg = [a, b].filter((s) => !s.aggregation);
    if (noAgg.length) {
      return blocked(
        REASONS.MISSING_AGGREGATION,
        `${noAgg.map((s) => s.table).join(", ")}: no aggregation validity declared for ${a.measureLabel || a.measure}`
      );
    }
    return blocked(
      REASONS.GRANULARITY,
      `${a.granularity} and ${b.granularity} share no reachable rung`
    );
  }
  return {
    kind: "aggregate_first",
    target: common[0],
    conversion: u.conversion,
  };
}

// WF-12 corollary over N series. `entries` may carry pre-failed tables
// (series construction already knows a table lacks the chosen measure):
//   [{ table, series } | { table, series: null, reason, detail }]
// A selection merges iff every pair merges or aggregate_firsts; the first
// blocked pair blocks the whole selection and is named in the verdict.
export function selectionVerdict(entries, { units = null } = {}) {
  const failed = entries.find((e) => !e.series);
  if (failed) {
    return {
      kind: "blocked",
      reason: failed.reason,
      detail: failed.detail,
      pair: [failed.table],
    };
  }
  const series = entries.map((e) => e.series);
  // ladder options valid for the WHOLE selection (drives the UI control)
  let levels = series.length ? reachableLevels(series[0]) : [];
  for (const s of series.slice(1))
    levels = levels.filter((l) => reachableLevels(s).includes(l));

  let kind = "merge";
  const conversions = [];
  for (let i = 0; i < series.length; i++) {
    for (let j = i + 1; j < series.length; j++) {
      const v = compareSeries(series[i], series[j], { units });
      if (v.kind === "blocked")
        return { ...v, pair: [series[i].table, series[j].table] };
      if (v.kind === "aggregate_first") kind = "aggregate_first";
      if (v.conversion) conversions.push(v.conversion);
    }
  }
  if (series.length > 1 && !levels.length) {
    return {
      kind: "blocked",
      reason: REASONS.GRANULARITY,
      detail: "no granularity fits every selected source",
    };
  }
  return { kind, levels, target: levels[0] || null, conversions };
}
