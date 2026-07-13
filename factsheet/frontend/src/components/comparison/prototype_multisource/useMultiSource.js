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
import { compareSeries, selectionVerdict, LADDER } from "../comparability.js";
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
  facetValuesForMeasure,
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
  // measure-first shortcut (reaction round 2): select every source that
  // provides the chosen measure
  const selectProviders = (providers) => setSelected([...providers]);
  // scenario-mode shortcut (reaction round 9): (de)select a whole dataset
  // family — the stand-in for a scenario until WF-14 harvests bundle links
  const toggleFamily = (tables, on) =>
    setSelected((cur) =>
      on
        ? [...new Set([...cur, ...tables])]
        : cur.filter((t) => !tables.includes(t))
    );
  const entriesFor = (tables) =>
    (catalog || []).filter((c) => tables.includes(c.table));
  const selectedEntries = useMemo(
    () => entriesFor(selected),
    [catalog, selected]
  );

  // ---- measure options: CATALOG-wide (measure-first flow, reaction round 1
  //      item 3) — pick a measure, then see which sources provide it; measures
  //      the current selection provides sort first ----
  const substanceDim = useMemo(
    () => (registry?.dimensions || []).find((d) => d.key === "substance"),
    [registry]
  );
  const measureOptions = useMemo(() => {
    const opts = [];
    const add = (space, value, table, label, aggregation) => {
      let o = opts.find((x) => x.space === space && x.value === value);
      if (!o) {
        o = { space, value, label, aggregation, providers: [] };
        opts.push(o);
      }
      o.providers.push(table);
    };
    for (const e of catalog || []) {
      for (const iri of e.substances) {
        const enumVal = (substanceDim?.values || []).find(
          (v) => expandCurie(registry, v.iri) === iri || v.iri === iri
        );
        add(
          "substance",
          iri,
          e.table,
          enumVal?.label || labelForIri(registry, substanceDim || {}, iri),
          enumVal?.aggregation || null
        );
      }
      for (const v of e.quantityKinds)
        add("quantity_kind", v, e.table, titleCase(v), null);
    }
    return opts
      .map((o) => ({
        ...o,
        selectedProviders: o.providers.filter((t) => selected.includes(t))
          .length,
      }))
      .sort(
        (a, b) =>
          b.selectedProviders - a.selectedProviders ||
          b.providers.length - a.providers.length
      );
  }, [catalog, selected, registry, substanceDim]);

  const [measureId, setMeasureId] = useState("");
  const measure = useMemo(
    () =>
      measureOptions.find((o) => `${o.space}:${o.value}` === measureId) || null,
    [measureOptions, measureId]
  );
  useEffect(() => {
    // keep a valid measure selected; prefer one the selection provides
    if (measure) return;
    const best =
      measureOptions.find((o) => o.selectedProviders > 0) || measureOptions[0];
    setMeasureId(best ? `${best.space}:${best.value}` : "");
  }, [measureOptions, measure]);

  // ---- units per (table, measure) for the WHOLE catalog (the rail's
  //      would-it-be-comparable indicators need unselected tables' units);
  //      the unit SELECT stays scoped to the selection (WF-02) ----
  const [unitsByTable, setUnitsByTable] = useState({});
  const [unit, setUnit] = useState("");
  useEffect(() => {
    if (!registry || !catalog?.length || !measure) {
      setUnitsByTable({});
      return;
    }
    let active = true;
    (async () => {
      try {
        const u = await unitsByTableForMeasure({
          registry,
          tables: catalog.map((c) => c.table),
          measure,
        });
        if (active) setUnitsByTable(u);
      } catch (e) {
        if (active) setUnitsByTable({});
      }
    })();
    return () => {
      active = false;
    };
  }, [registry, catalog, measure]);
  const unitOptions = useMemo(
    () => [...new Set(selected.flatMap((t) => unitsByTable[t] || []))],
    [unitsByTable, selected]
  );
  useEffect(() => {
    setUnit((cur) => (unitOptions.includes(cur) ? cur : unitOptions[0] || ""));
  }, [unitOptions]);

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
    // shared = every selected source populates the dimension — grouping by a
    // partial dimension silently drops the sources that lack it (transparency
    // ask, reaction round 1 item 3)
    const sharedAll = (k) =>
      selected.length > 0 &&
      selected.every((t) => (availByTable[t] || new Set()).has(k));
    return [
      { key: "source", label: "Source (table)", shared: true, isSource: true },
      ...dims.map((d) => ({
        key: d.key,
        label: titleCase(d.key),
        shared: sharedAll(d.key),
      })),
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
  // one catalog entry's series for the chosen measure — or null + WF-12 reason
  const entrySeries = (e) => {
    const declaresSubstance = e.substances.length > 0;
    const declaresQk = e.quantityKinds.length > 0;
    if (!declaresSubstance && !declaresQk) {
      // eu_leg live case: metadata declares the measure but the mapping never
      // emits it — treated as its own measure space until WF-21 lands.
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
  };

  const verdictInput = useMemo(
    () => (measure ? selectedEntries.map(entrySeries) : []),
    [selectedEntries, measure, unitsByTable, unit] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const verdict = useMemo(
    () =>
      verdictInput.length
        ? selectionVerdict(verdictInput, { units: registry?.units || null })
        : null,
    [verdictInput, registry]
  );

  // ---- candidate indicators (reaction round 1, items 2+3): for EVERY catalog
  //      table, what would happen if it joined the current selection — same
  //      pure contract, surfaced in the selection window ----
  const candidates = useMemo(() => {
    if (!measure || !catalog) return {};
    const selSeries = verdictInput.filter((x) => x.series).map((x) => x.series);
    const out = {};
    for (const c of catalog) {
      const entry = entrySeries(c);
      if (!entry.series) {
        out[c.table] = {
          kind: "no_data",
          reason: entry.reason,
          detail: entry.detail,
        };
        continue;
      }
      let kind = "merge";
      let reason = null;
      let detail = null;
      for (const s of selSeries) {
        if (s.table === c.table) continue;
        const v = compareSeries(entry.series, s, {
          units: registry?.units || null,
        });
        if (v.kind === "blocked") {
          kind = "blocked";
          reason = v.reason;
          detail = v.detail;
          break;
        }
        if (v.kind === "aggregate_first") kind = "aggregate_first";
      }
      out[c.table] = { kind, reason, detail };
    }
    return out;
  }, [catalog, measure, verdictInput, unitsByTable, unit, registry]); // eslint-disable-line react-hooks/exhaustive-deps

  // ---- facet-conflation guard (reaction round 8): a value's meaning is the
  //      COMBINATION of its annotations (WF-04). If the chosen measure's
  //      observations spread over ≥2 values of a facet dimension the chart is
  //      not grouped by, those values are summed into one series — warn and
  //      offer the fixing group-by instead of plotting silently. ----
  const [facetSpread, setFacetSpread] = useState({});
  useEffect(() => {
    if (!registry || !selected.length || !measure) {
      setFacetSpread({});
      return;
    }
    let active = true;
    facetValuesForMeasure({ registry, tables: selected, measure })
      .then((s) => active && setFacetSpread(s))
      .catch(() => active && setFacetSpread({}));
    return () => {
      active = false;
    };
  }, [registry, selected, measure]);
  // facet filters (round 9): pin a spread facet to one value ("all" sums, a
  // value filters, "none" keeps only observations without the facet) — the
  // alternative to grouping by it, so not every group-by choice warns
  const [facetFilters, setFacetFilters] = useState({});
  const setFacetFilter = (key, choice) =>
    setFacetFilters((cur) => ({ ...cur, [key]: choice }));
  useEffect(() => {
    // drop filters whose facet/value the new measure/selection no longer has
    setFacetFilters((cur) => {
      const next = {};
      for (const [k, v] of Object.entries(cur)) {
        const vals = facetSpread[k] || [];
        if (v === "all" || v === "none" || vals.some((x) => x.iri === v))
          next[k] = v;
      }
      return next;
    });
  }, [facetSpread]);
  const conflations = useMemo(
    () =>
      Object.entries(facetSpread)
        .filter(
          ([key, vals]) =>
            vals.length > 1 &&
            key !== groupKey &&
            (facetFilters[key] || "all") === "all"
        )
        .map(([key, vals]) => ({
          key,
          label: titleCase(key),
          values: vals.map((v) => v.label),
        })),
    [facetSpread, groupKey, facetFilters]
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

  // stale-chart detection (reaction round 1, item 4): the chart remembers the
  // parameters it was run with; any change dims it until re-run
  const paramsKey = JSON.stringify({
    selected: [...selected].sort(),
    measureId,
    unit,
    granularity,
    groupKey,
    facetFilters,
  });
  const [ranKey, setRanKey] = useState(null);
  const [ranGranularity, setRanGranularity] = useState(null);
  const [ranSummary, setRanSummary] = useState(null);
  const stale = !!rows && ranKey !== paramsKey;

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
        facetFilters,
      });
      setLastQuery(q);
      const data = await postSparql(q);
      setRows(data?.results?.bindings || []);
      setRanKey(paramsKey);
      setRanGranularity(granularity);
      // snapshot of WHAT this run plotted and WHAT was done to the data —
      // feeds the generated chart title + the computation statement (round 6);
      // snapshotted so title/statement stay truthful while parameters drift
      setRanSummary({
        measureLabel: measure?.label || null,
        space: measure?.space || null,
        unit: unit || null,
        granularity,
        groupKey,
        groupLabel:
          groupKey === "source"
            ? "source"
            : titleCase(
                groupOptions.find((o) => o.key === groupKey)?.label || groupKey
              ),
        sources: selectedEntries.map((e) => ({
          table: e.table,
          title: e.title,
        })),
        // per-source transformation story: aggregation is the only
        // calculation the tool performs today (unit conversion is the WF-13
        // seam and stays inert until the registry serves units:)
        transforms: verdictInput
          .filter(
            (e) =>
              e.series &&
              e.series.granularity &&
              e.series.granularity !== granularity
          )
          .map((e) => ({
            table: e.table,
            from: e.series.granularity,
            to: granularity,
            fn:
              measure?.aggregation === "mean"
                ? "averaged (AVG)"
                : "summed (SUM)",
            hinted: !!measure?.aggregation,
          })),
        conversions: verdict?.conversions || [],
        filters: Object.entries(facetFilters)
          .filter(([, v]) => v && v !== "all")
          .map(([k, v]) => ({
            label: titleCase(k),
            value:
              v === "none"
                ? "without this facet"
                : (facetSpread[k] || []).find((x) => x.iri === v)?.label || v,
          })),
      });
    } catch (e) {
      setErr(e?.message || "Query failed");
    } finally {
      setRunning(false);
    }
  };

  // notices: standing caveats stated on the chart (WF-06). Per-source
  // aggregation statements moved into ranSummary.transforms (round 6) so the
  // computation story is run-snapshotted, not live-drifting.
  const notices = useMemo(() => {
    const out = [];
    for (const c of conflations) {
      out.push(
        `Mixed ${c.label} values (${c.values.join(" · ")}) are summed within each series — group by ${c.label} to keep them apart.`
      );
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
  }, [granularity, selectedEntries, conflations]);

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
    selectProviders,
    toggleFamily,
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
    candidates,
    conflations,
    facetSpread,
    facetFilters,
    setFacetFilter,
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
    stale,
    ranGranularity,
    ranSummary,
    notices,
    unmappedFootnotes,
    bucketLabel,
  };
}
