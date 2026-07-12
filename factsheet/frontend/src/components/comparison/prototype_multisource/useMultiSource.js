// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// PROTOTYPE (wayfinder WF-07) — one shared state machine behind all three UI
// variants, so flipping variants keeps the selection. The variants only
// differ in presentation; the semantics here are the decided ones:
//   WF-02 merged result set, source as first-class dimension (default
//         group-by when >1 source), unit filter spans all sources;
//   WF-05 incompleteness report (registry unmapped_columns) → badges;
//   WF-06 granularity ladder, aggregation function from the registry hint;
//   WF-12 pure comparability verdict (../comparability.js), blocked
//         selections stay selectable and the chart explains why.

import { useEffect, useMemo, useState } from "react";
import useRegistry from "../useRegistry.js";
import { labelForIri, expandCurie } from "../registryQuery.js";
import { selectionVerdict, LADDER } from "../comparability.js";
import {
  postSparql,
  fetchMappedTables,
  fetchTableMeta,
  familyOf,
  tablesWithDimension,
  measuresByTable,
  unitsByTableForMeasure,
  askDimension,
  buildMergedQuery,
  bucketLabel,
} from "./protoData.js";

const titleCase = (k) =>
  String(k)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

// dimensions that are machinery, not group-by candidates
const NON_GROUP = new Set([
  "quantity_value",
  "unit",
  "substance",
  "quantity_kind",
  "time_step",
  "scenario_year",
]);

export default function useMultiSource() {
  const {
    registry,
    loading: registryLoading,
    error: registryError,
  } = useRegistry();

  // ---- catalog: mapped tables + oemetadata + facts + unmapped report ----
  const [catalog, setCatalog] = useState(null);
  useEffect(() => {
    if (!registry) return;
    let active = true;
    (async () => {
      const byKey = Object.fromEntries(
        (registry.dimensions || []).map((d) => [d.key, d])
      );
      const [tables, hasTs, hasYear, subst, qk] = await Promise.all([
        fetchMappedTables(registry),
        tablesWithDimension(registry, byKey.time_step),
        tablesWithDimension(registry, byKey.scenario_year),
        measuresByTable(registry, byKey.substance),
        measuresByTable(registry, byKey.quantity_kind),
      ]);
      const metas = await Promise.all(tables.map(fetchTableMeta));
      if (!active) return;
      setCatalog(
        tables.map((t, i) => ({
          table: t,
          family: familyOf(t),
          ...metas[i],
          unmapped: (registry.unmapped_columns || {})[t] || [],
          substances: subst[t] || [],
          quantityKinds: qk[t] || [],
          // native granularity: hourly rows if time_step is mapped, else the
          // declared scenario_year, else no temporal declaration at all
          granularity: hasTs.has(t) ? "hour" : hasYear.has(t) ? "year" : null,
        }))
      );
    })();
    return () => {
      active = false;
    };
  }, [registry]);

  // ---- selection ----
  const [selected, setSelected] = useState([
    "amiris_germany2019_day_ahead_market_single_zone",
  ]);
  const toggle = (t) =>
    setSelected((cur) =>
      cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t]
    );
  const entriesFor = (tables) =>
    (catalog || []).filter((c) => tables.includes(c.table));
  const selectedEntries = useMemo(
    () => entriesFor(selected),
    [catalog, selected]
  );

  // ---- measure options = union over the selection, both spaces ----
  const substanceDim = useMemo(
    () => (registry?.dimensions || []).find((d) => d.key === "substance"),
    [registry]
  );
  const measureOptions = useMemo(() => {
    const opts = [];
    for (const e of selectedEntries) {
      for (const iri of e.substances) {
        const found = opts.find(
          (o) => o.space === "substance" && o.value === iri
        );
        if (found) found.tables.push(e.table);
        else {
          const enumVal = (substanceDim?.values || []).find(
            (v) => expandCurie(registry, v.iri) === iri || v.iri === iri
          );
          opts.push({
            space: "substance",
            value: iri,
            tables: [e.table],
            label:
              enumVal?.label || labelForIri(registry, substanceDim || {}, iri),
            aggregation: enumVal?.aggregation || null,
          });
        }
      }
      for (const v of e.quantityKinds) {
        const found = opts.find(
          (o) => o.space === "quantity_kind" && o.value === v
        );
        if (found) found.tables.push(e.table);
        else
          opts.push({
            space: "quantity_kind",
            value: v,
            tables: [e.table],
            label: titleCase(v),
            aggregation: null,
          });
      }
    }
    // most widely shared first — the cross-source measures are the point
    return opts.sort((a, b) => b.tables.length - a.tables.length);
  }, [selectedEntries, registry, substanceDim]);

  const [measureId, setMeasureId] = useState("");
  const measure = useMemo(
    () =>
      measureOptions.find((o) => `${o.space}:${o.value}` === measureId) || null,
    [measureOptions, measureId]
  );
  useEffect(() => {
    // keep a valid measure selected; prefer one every selected source shares
    if (measure) return;
    const best = measureOptions[0];
    setMeasureId(best ? `${best.space}:${best.value}` : "");
  }, [measureOptions, measure]);

  // ---- units per (table, measure); options span ALL selected sources ----
  const [unitsByTable, setUnitsByTable] = useState({});
  const [unit, setUnit] = useState("");
  useEffect(() => {
    if (!registry || !selected.length || !measure) {
      setUnitsByTable({});
      return;
    }
    let active = true;
    (async () => {
      try {
        const u = await unitsByTableForMeasure({
          registry,
          tables: selected,
          measure,
        });
        if (!active) return;
        setUnitsByTable(u);
        const all = [...new Set(Object.values(u).flat())];
        setUnit((cur) => (all.includes(cur) ? cur : all[0] || ""));
      } catch (e) {
        if (active) setUnitsByTable({});
      }
    })();
    return () => {
      active = false;
    };
  }, [registry, selected, measure]);
  const unitOptions = useMemo(
    () => [...new Set(Object.values(unitsByTable).flat())],
    [unitsByTable]
  );

  // ---- group-by discovery: union of per-table ASKs (WF-07 spec) ----
  const [availByTable, setAvailByTable] = useState({});
  useEffect(() => {
    if (!registry || !selected.length) return;
    let active = true;
    const dims = (registry.dimensions || []).filter(
      (d) => !NON_GROUP.has(d.key)
    );
    (async () => {
      const perTable = await Promise.all(
        selected.map(async (t) => {
          const asks = await Promise.all(
            dims.map(async (d) => [d.key, await askDimension(registry, t, d)])
          );
          return [t, new Set(asks.filter(([, ok]) => ok).map(([k]) => k))];
        })
      );
      if (active) setAvailByTable(Object.fromEntries(perTable));
    })();
    return () => {
      active = false;
    };
  }, [registry, selected]);

  const groupOptions = useMemo(() => {
    const union = new Set();
    for (const t of selected)
      for (const k of availByTable[t] || []) union.add(k);
    const dims = (registry?.dimensions || []).filter((d) => union.has(d.key));
    return [
      { key: "source", label: "Source (table)", isSource: true },
      ...dims.map((d) => ({ key: d.key, label: titleCase(d.key) })),
    ];
  }, [registry, selected, availByTable]);

  const [groupKey, setGroupKey] = useState("source");
  useEffect(() => {
    // WF-02: source becomes the default group-by whenever the selection grows
    // past one source (the user may regroup afterwards)
    if (selected.length > 1) setGroupKey("source");
  }, [selected]);
  useEffect(() => {
    // repair a group key the new selection no longer offers
    setGroupKey((cur) =>
      groupOptions.find((o) => o.key === cur)
        ? cur
        : groupOptions[1]?.key || "source"
    );
  }, [groupOptions]);

  // ---- series + verdict (pure — ../comparability.js) ----
  const verdictInput = useMemo(() => {
    if (!measure) return [];
    return selectedEntries.map((e) => {
      const declaresSubstance = e.substances.length > 0;
      const declaresQk = e.quantityKinds.length > 0;
      if (!declaresSubstance && !declaresQk) {
        // PROTOTYPE ASSUMPTION (not pinned by WF-12): a table with NO measure
        // dimension is its own measure space → blocked against everything.
        // eu_leg is the live case; reaction wanted.
        return {
          table: e.table,
          series: null,
          reason: "measure spaces not aligned",
          detail: `${e.table} declares no measure dimension (neither substance nor quantity_kind)`,
        };
      }
      const inSpace =
        measure.space === "substance" ? e.substances : e.quantityKinds;
      if (!inSpace.length) {
        return {
          table: e.table,
          series: null,
          reason: "measure spaces not aligned",
          detail: `${e.table} annotates ${declaresSubstance ? "substance" : "quantity_kind"}, the chosen measure lives in ${measure.space}`,
        };
      }
      if (!inSpace.includes(measure.value)) {
        return {
          table: e.table,
          series: null,
          reason: "measure mismatch",
          detail: `${e.table} does not report ${measure.label}`,
        };
      }
      const tableUnits = unitsByTable[e.table] || [];
      return {
        table: e.table,
        series: {
          table: e.table,
          space: measure.space,
          measure: measure.value,
          measureLabel: measure.label,
          unit: tableUnits.includes(unit) ? unit : tableUnits[0] || null,
          granularity: e.granularity,
          aggregation: measure.aggregation,
        },
      };
    });
  }, [selectedEntries, measure, unitsByTable, unit]);

  const verdict = useMemo(
    () =>
      verdictInput.length
        ? selectionVerdict(verdictInput, { units: registry?.units || null })
        : null,
    [verdictInput, registry]
  );

  // ---- granularity ladder ----
  const ladder = useMemo(() => {
    const ok =
      verdict?.kind && verdict.kind !== "blocked" ? verdict.levels : [];
    return LADDER.map((l) => ({
      level: l,
      enabled: ok.includes(l) && l !== "week", // no WEEK() through ontop — see protoData.js
    }));
  }, [verdict]);
  const [granularity, setGranularity] = useState("year");
  useEffect(() => {
    const enabled = ladder.filter((l) => l.enabled).map((l) => l.level);
    if (enabled.length && !enabled.includes(granularity))
      setGranularity(enabled[enabled.length - 1]);
  }, [ladder, granularity]);

  // ---- run ----
  const [rows, setRows] = useState(null);
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState(null);
  const [lastQuery, setLastQuery] = useState("");
  const [chartType, setChartType] = useState("line");

  const run = async () => {
    if (!registry || !selected.length || verdict?.kind === "blocked") return;
    setRunning(true);
    setErr(null);
    setRows(null);
    try {
      const q = buildMergedQuery({
        registry,
        tables: selected,
        measure,
        unit,
        granularity,
        groupKey,
        agg: measure?.aggregation,
      });
      setLastQuery(q);
      const data = await postSparql(q);
      setRows(data?.results?.bindings || []);
    } catch (e) {
      setErr(e?.message || "Query failed");
    } finally {
      setRunning(false);
    }
  };

  // notices: what the tool did / will do — stated on the chart (WF-06/WF-12)
  const notices = useMemo(() => {
    const out = [];
    for (const e of verdictInput) {
      if (
        e.series &&
        e.series.granularity &&
        e.series.granularity !== granularity
      ) {
        out.push(
          `${e.table} (${e.series.granularity}ly) ${measure?.aggregation === "mean" ? "averaged" : "summed"} to ${granularity} — registry aggregation hint: ${measure?.aggregation || "sum (fallback)"}`
        );
      }
    }
    if (
      ["day", "month"].includes(granularity) &&
      selectedEntries.some((e) => e.family.startsWith("AMIRIS"))
    ) {
      out.push(
        "FAME settlement bookings (730-h months) don't align with calendar periods — sparse money series show bookings-in-period (WF-06 caveat)."
      );
    }
    return out;
  }, [verdictInput, granularity, measure, selectedEntries]);

  const unmappedFootnotes = useMemo(
    () =>
      selectedEntries
        .filter((e) => e.unmapped.length)
        .map((e) => ({
          table: e.table,
          count: e.unmapped.length,
          details: e.unmapped,
        })),
    [selectedEntries]
  );

  return {
    registry,
    registryLoading,
    registryError,
    catalog,
    selected,
    toggle,
    selectedEntries,
    measureOptions,
    measure,
    measureId,
    setMeasureId,
    unitOptions,
    unitsByTable,
    unit,
    setUnit,
    groupOptions,
    groupKey,
    setGroupKey,
    verdict,
    verdictInput,
    ladder,
    granularity,
    setGranularity,
    run,
    running,
    rows,
    err,
    lastQuery,
    chartType,
    setChartType,
    notices,
    unmappedFootnotes,
    bucketLabel,
  };
}
