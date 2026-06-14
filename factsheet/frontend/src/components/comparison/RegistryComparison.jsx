// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// Registry-driven quantitative comparison (beta). Works for ANY annotated table:
// dimensions, predicates, value IRIs and labels come from /oekg/registry/, with
// ontology labels/definitions loaded from the TIB Terminology Service.
//
// UX:
//   * Only dimensions/presets the table actually populates are shown (discovery).
//   * Presets give one-click → result; a plain-language customiser with ontology
//     labels (not variable keys).
//   * Unit selector — values are only summed within one unit (mixing is wrong).
//   * "How it works" decomposition reveal tucked into an accordion.

import React, { useEffect, useMemo, useState } from "react";
import ReactECharts from "echarts-for-react";
import axios from "axios";
import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Stack from "@mui/material/Stack";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Tooltip from "@mui/material/Tooltip";
import Link from "@mui/material/Link";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import Alert from "@mui/material/Alert";
import LinearProgress from "@mui/material/LinearProgress";
import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

import conf from "../../conf.json";
import CSRFToken from "../csrfToken.js";
import useRegistry from "./useRegistry.js";
import {
  buildComparisonQuery, labelForIri, expandCurie,
  dimensionAskQuery, valueFrequencyQuery,
} from "./registryQuery.js";
import { resolveTerms } from "./tibTerms.js";

const PALETTE = [
  "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
  "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
];
const DELIM = " | ";
const ROWS_SCHEMA = "model_draft";

const titleCase = (k) => k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
const shorten = (s) => (s && s.startsWith("http") ? s.split("/").pop() : s);
const cellValue = (registry, dim, row) => {
  const b = row[dim.key];
  if (!b) return null;
  return dim.object_kind === "iri" ? labelForIri(registry, dim, b.value) : b.value;
};

function TermChip({ info, fallbackLabel, fullIri, color }) {
  const label = info?.label || shorten(fallbackLabel);
  const desc = info?.description || "Loading definition…";
  return (
    <Tooltip arrow placement="top" title={<Typography variant="body2" sx={{ p: 0.5 }}>{desc}</Typography>}>
      <Chip label={label} size="small"
        component={fullIri ? Link : "div"} href={fullIri || undefined} target="_blank" clickable={!!fullIri}
        variant="outlined" sx={{ cursor: fullIri ? "pointer" : "help", fontWeight: 600, borderColor: color, color }} />
    </Tooltip>
  );
}

export default function RegistryComparison() {
  const { registry, loading: registryLoading, error: registryError } = useRegistry();

  const [table, setTable] = useState("ariadne2_data_with_labels");
  const [xKey, setXKey] = useState("scenario_year");
  const [stackKey, setStackKey] = useState("technology");
  const [unitOptions, setUnitOptions] = useState([]);
  const [unit, setUnit] = useState("");
  const [quantityOptions, setQuantityOptions] = useState([]); // [{value,count}] most common first
  const [primaryQuantity, setPrimaryQuantity] = useState(""); // "" = all quantities
  const [chartType, setChartType] = useState("stacked"); // stacked | grouped | line
  const [availableKeys, setAvailableKeys] = useState(null); // Set | null(=show all)
  const [discovering, setDiscovering] = useState(false);
  const [rawString, setRawString] = useState(null);
  const [segments, setSegments] = useState([]);
  const [rows, setRows] = useState(null);
  const [terms, setTerms] = useState({});
  const [dimTerms, setDimTerms] = useState({});
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState(null);
  const [lastQuery, setLastQuery] = useState("");

  const allAxisDims = useMemo(
    () => (registry?.dimensions || []).filter((d) => !["quantity_value", "unit"].includes(d.key)),
    [registry]
  );
  const axisDims = useMemo(
    () => (availableKeys ? allAxisDims.filter((d) => availableKeys.has(d.key)) : allAxisDims),
    [allAxisDims, availableKeys]
  );
  const dimLabel = (d) => (d?.concept && dimTerms[d.concept]?.label) || titleCase(d?.key || "");

  // short inline hint: how rows qualify for this dimension
  const dimSourceShort = (d) =>
    !d ? "" :
    d.value_space === "iamc_tokens" ? "matched from variable-string tokens" :
    d.object_kind === "literal" ? "raw value of the column" :
    "controlled value → ontology IRI";
  // full hover: how rows qualify + which predicate + ontology definition
  const dimTooltip = (d) => {
    if (!d) return "";
    const how =
      d.value_space === "iamc_tokens"
        ? `Qualifies rows whose variable string contains a ${titleCase(d.key)} token (e.g. ${(d.values || []).slice(0, 4).map((v) => v.code).join(", ")}).`
        : d.object_kind === "literal"
        ? `Uses the raw value of the “${titleCase(d.key)}” column.`
        : `Qualifies rows whose value maps to an ontology IRI (controlled vocabulary).`;
    const def = d.concept && dimTerms[d.concept]?.description;
    return `${how} — predicate ${d.predicate}.${def ? " · " + def : ""}`;
  };

  const tokenIndex = useMemo(() => {
    const idx = {};
    for (const d of registry?.dimensions || []) {
      if (d.value_space !== "iamc_tokens") continue;
      for (const v of d.values || []) idx[v.code.toLowerCase()] = { ...v, dimension: d.key };
    }
    return idx;
  }, [registry]);

  const postSparql = async (query) => {
    const res = await axios.post(conf.obdi, query, {
      headers: {
        "X-CSRFToken": CSRFToken(),
        Accept: "application/sparql-results+json",
        "Content-Type": "application/sparql-query",
      },
    });
    return res.data;
  };

  const timeDim = useMemo(
    () => axisDims.find((d) => d.key === "scenario_year") ||
          axisDims.find((d) => (d.datatype || "").includes("gYear")) || null,
    [axisDims]
  );
  // dimensions offered as breakdowns/axes (quantity is the primary filter, not a breakdown)
  const breakdownDims = useMemo(
    () => axisDims.filter((d) => !(primaryQuantity && d.key === "quantity_kind")),
    [axisDims, primaryQuantity]
  );
  const presets = useMemo(() => {
    if (!timeDim) return [];
    return breakdownDims
      .filter((d) => d.key !== timeDim.key &&
        (d.object_kind !== "iri" || (d.values || []).length > 0)) // literal dims always groupable
      .map((d) => ({ name: `${titleCase(d.key)} over ${titleCase(timeDim.key)}`, x: timeDim.key, stack: d.key }));
  }, [breakdownDims, timeDim]);

  // dimension concept labels (for the controls)
  useEffect(() => {
    if (!registry) return;
    let active = true;
    resolveTerms((registry.dimensions || []).map((d) => d.concept).filter(Boolean))
      .then((m) => active && setDimTerms(m));
    return () => { active = false; };
  }, [registry]);

  // DISCOVERY: which dimensions/units does THIS table populate?
  useEffect(() => {
    if (!registry) return;
    let active = true;
    setDiscovering(true); setAvailableKeys(null); setRows(null);
    (async () => {
      const t = table.trim();
      // availability via ASK per dimension
      let avail = null;
      try {
        const res = await Promise.all(allAxisDims.map(async (dm) => {
          try { const r = await postSparql(dimensionAskQuery({ registry, table: t, dim: dm })); return [dm.key, !!r.boolean]; }
          catch { return [dm.key, true]; }
        }));
        avail = new Set(res.filter(([, ok]) => ok).map(([k]) => k));
      } catch (e) { avail = null; }
      // primary quantity options (the first IAMC segment), most common first
      let quants = [];
      try {
        const qd = allAxisDims.find((d) => d.key === "quantity_kind");
        if (qd) {
          const r = await postSparql(valueFrequencyQuery({ registry, table: t, dim: qd }));
          quants = (r.results?.bindings || []).map((b) => ({ value: b.v.value, count: +(b.c?.value || 0) }));
        }
      } catch (e) { /* ignore */ }
      if (!active) return;
      setAvailableKeys(avail);
      setQuantityOptions(quants);
      setPrimaryQuantity((cur) => (quants.find((q) => q.value === cur) ? cur : (quants[0]?.value || "")));
      if (avail) {
        // quantity_kind is the PRIMARY filter, not a breakdown
        const keys = [...avail].filter((k) => k !== "quantity_kind");
        setXKey((cur) => (avail.has(cur) ? cur : (avail.has("scenario_year") ? "scenario_year" : keys[0])) || cur);
        setStackKey((cur) => (avail.has(cur) && cur !== "quantity_kind" ? cur : (keys.find((k) => k !== "scenario_year") || keys[0])) || cur);
      }
      setDiscovering(false);
    })();
    return () => { active = false; };
  }, [registry, table, allAxisDims]);

  // UNITS — follow the chosen quantity (the unit is determined by the quantity)
  useEffect(() => {
    if (!registry) return;
    let active = true;
    (async () => {
      const unitDim = (registry.dimensions || []).find((d) => d.key === "unit");
      const qkDim = allAxisDims.find((d) => d.key === "quantity_kind");
      if (!unitDim) return;
      try {
        const d = await postSparql(valueFrequencyQuery({
          registry, table: table.trim(), dim: unitDim,
          scopeDim: primaryQuantity ? qkDim : null, scopeValue: primaryQuantity || null,
        }));
        const us = (d.results?.bindings || []).map((b) => b.v.value);
        if (!active) return;
        setUnitOptions(us);
        setUnit((cur) => (us.includes(cur) ? cur : (us[0] || "")));
      } catch (e) { if (active) { setUnitOptions([]); setUnit(""); } }
    })();
    return () => { active = false; };
  }, [registry, table, primaryQuantity, allAxisDims]);

  // sample row + IAMC decomposition (only if present)
  useEffect(() => {
    if (!registry) return;
    let active = true;
    (async () => {
      try {
        const res = await axios.get(`/api/v0/schema/${ROWS_SCHEMA}/tables/${table.trim()}/rows/?limit=80`);
        const data = Array.isArray(res.data) ? res.data : [];
        const withStr = data.filter((r) => r.iamc_full_string);
        if (!withStr.length) { if (active) { setRawString(null); setSegments([]); } return; }
        const best = withStr.sort((a, b) => b.iamc_full_string.split("|").length - a.iamc_full_string.split("|").length)[0];
        const raw = best.iamc_full_string;
        const segs = raw.split(DELIM).map((s) => s.trim()).filter(Boolean)
          .map((seg) => ({ seg, match: tokenIndex[seg.toLowerCase()] || null }));
        if (!active) return;
        setRawString(raw); setSegments(segs);
        const map = await resolveTerms(segs.map((s) => s.match?.iri).filter(Boolean));
        if (active) setTerms((p) => ({ ...p, ...map }));
      } catch (e) { if (active) { setRawString(null); setSegments([]); } }
    })();
    return () => { active = false; };
  }, [registry, table, tokenIndex]);

  const run = async (xk = xKey, sk = stackKey, u = unit, q = primaryQuantity) => {
    setXKey(xk); setStackKey(sk);
    setRunning(true); setErr(null); setRows(null);
    try {
      const filters = {};
      const dimset = new Set([xk, sk]);
      if (u) { dimset.add("unit"); filters.unit = [u]; }
      // scope to the primary quantity (unless it IS an axis here)
      if (q && xk !== "quantity_kind" && sk !== "quantity_kind") {
        dimset.add("quantity_kind"); filters.quantity_kind = [q];
      }
      const query = buildComparisonQuery({ registry, tables: [table.trim()], dims: [...dimset], filters });
      setLastQuery(query);
      const data = await postSparql(query);
      const bindings = data?.results?.bindings || [];
      setRows(bindings);
      const stackDim = allAxisDims.find((d) => d.key === sk);
      if (stackDim?.object_kind === "iri") {
        const map = await resolveTerms(bindings.map((r) => r[sk]?.value).filter(Boolean));
        setTerms((p) => ({ ...p, ...map }));
      }
    } catch (e) { setErr(e?.message || "Query failed"); } finally { setRunning(false); }
  };

  // preset: pick the breakdown AND the most relevant unit (for the current
  // primary quantity), then run scoped to that quantity.
  const runPreset = async (p) => {
    setXKey(p.x); setStackKey(p.stack);
    const unitDim = (registry.dimensions || []).find((d) => d.key === "unit");
    const qkDim = allAxisDims.find((d) => d.key === "quantity_kind");
    let u = unit;
    try {
      const d = await postSparql(valueFrequencyQuery({
        registry, table: table.trim(), dim: unitDim,
        scopeDim: primaryQuantity ? qkDim : null, scopeValue: primaryQuantity || null,
      }));
      const us = (d.results?.bindings || []).map((b) => b.v.value);
      setUnitOptions(us);
      u = us[0] || "";
      setUnit(u);
    } catch (e) { /* keep current unit */ }
    run(p.x, p.stack, u, primaryQuantity);
  };

  const seriesLabel = (fullIri, fallback) => {
    const lbl = (fullIri && terms[fullIri]?.label) || fallback;
    return shorten(lbl);
  };

  const { option, stackValues } = useMemo(() => {
    if (!rows || !registry) return { option: null, stackValues: [] };
    const xDim = allAxisDims.find((d) => d.key === xKey);
    const stackDim = allAxisDims.find((d) => d.key === stackKey);
    if (!xDim || !stackDim) return { option: null, stackValues: [] };
    const xVals = [...new Set(rows.map((r) => cellValue(registry, xDim, r)).filter((v) => v != null))].sort();
    const stacks = []; const matrix = {};
    for (const r of rows) {
      const x = cellValue(registry, xDim, r);
      const sFull = stackDim.object_kind === "iri" ? r[stackDim.key]?.value : null;
      const sLabel = seriesLabel(sFull, cellValue(registry, stackDim, r));
      const val = parseFloat(r.value?.value);
      if (x == null || sLabel == null || Number.isNaN(val)) continue;
      if (!stacks.find((s) => s.label === sLabel)) stacks.push({ label: sLabel, fullIri: sFull });
      matrix[sLabel] = matrix[sLabel] || {}; matrix[sLabel][x] = (matrix[sLabel][x] || 0) + val;
    }
    const isLine = chartType === "line";
    const stackId = chartType === "stacked" ? "total" : undefined;
    const opt = {
      tooltip: { trigger: "axis", axisPointer: { type: isLine ? "line" : "shadow" } },
      legend: { type: "scroll", top: 0 },
      grid: { left: 80, right: 20, bottom: 40, top: 40 },
      xAxis: { type: "category", data: xVals, name: titleCase(xDim.key) },
      yAxis: { type: "value", name: unit || "value" },
      series: stacks.map((s, i) => ({
        name: s.label, type: isLine ? "line" : "bar",
        ...(stackId ? { stack: stackId } : {}),
        emphasis: { focus: "series" }, smooth: isLine,
        itemStyle: { color: PALETTE[i % PALETTE.length] }, data: xVals.map((x) => matrix[s.label]?.[x] ?? 0),
      })),
    };
    return { option: opt, stackValues: stacks };
  }, [rows, registry, allAxisDims, xKey, stackKey, unit, terms, chartType]);

  if (registryLoading) return <LinearProgress />;
  if (registryError) return <Alert severity="error">Could not load the registry from {conf.dimensionRegistry}.</Alert>;

  const xDimObj = allAxisDims.find((d) => d.key === xKey);
  const stackDimObj = allAxisDims.find((d) => d.key === stackKey);

  return (
    <Box sx={{ px: 2 }}>
      {/* PRIMARY VARIABLE — the top-level measured quantity; scopes everything
          below. Only shown when the dataset actually has a quantity dimension
          (so single-variable / typed tables aren't cluttered with it). */}
      {quantityOptions.length > 0 && (
      <Card variant="outlined" sx={{ mb: 2, borderColor: "primary.main" }}>
        <CardContent sx={{ py: 1.5 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField select label="Primary variable (what to measure)" value={primaryQuantity} fullWidth size="small"
                helperText="the measured quantity — scopes the unit, options & chart"
                onChange={(e) => {
                  const v = e.target.value;
                  setPrimaryQuantity(v);
                  if (v && stackKey === "quantity_kind") {
                    const alt = axisDims.find((d) => d.key !== "quantity_kind" && d.key !== xKey);
                    if (alt) setStackKey(alt.key);
                  }
                }}>
                <MenuItem value="">(all variables — mixed)</MenuItem>
                {quantityOptions.map((q) => (
                  <MenuItem key={q.value} value={q.value}>{titleCase(q.value)}{q.count ? ` (${q.count})` : ""}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">
                {primaryQuantity
                  ? <>Scoped to <b>{titleCase(primaryQuantity)}</b> — pick a unit + a breakdown below.</>
                  : <>All variables (mixed units) — pick one to focus the analysis and shrink the options.</>}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
      )}

      {/* PRESETS */}
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>Quick comparisons (one click):</Typography>
      <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ mb: 2 }}>
        {discovering && <Chip label="finding available comparisons…" size="small" />}
        {!discovering && presets.length === 0 && <Typography variant="body2" color="text.secondary">No presets for this table.</Typography>}
        {presets.map((p) => (
          <Button key={p.name} size="small" variant="outlined" disabled={running} onClick={() => runPreset(p)}>{p.name}</Button>
        ))}
      </Stack>

      {/* CUSTOMISER */}
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="body1" sx={{ mb: 1.5 }}>
            Show the total <b>value</b>{unit ? <> in <b>{unit}</b></> : null} across{" "}
            <Tooltip title={dimTooltip(xDimObj)}><b style={{ borderBottom: "1px dotted" }}>{dimLabel(xDimObj)}</b></Tooltip>
            , grouped by{" "}
            <Tooltip title={dimTooltip(stackDimObj)}><b style={{ borderBottom: "1px dotted" }}>{dimLabel(stackDimObj)}</b></Tooltip>.
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <TextField label="Dataset (table)" value={table} onChange={(e) => setTable(e.target.value)} fullWidth size="small" helperText="one dataset at a time" />
            </Grid>
            <Grid item xs={6} md={3}>
              <TextField select label="Across (x-axis)" value={xKey} fullWidth size="small"
                helperText={dimSourceShort(xDimObj) || "usually time/years"} onChange={(e) => setXKey(e.target.value)}>
                {breakdownDims.map((d) => <MenuItem key={d.key} value={d.key}>{dimLabel(d)}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={6} md={3}>
              <TextField select label="Grouped by (bars)" value={stackKey} fullWidth size="small"
                helperText={dimSourceShort(stackDimObj) || "dimension to break down"} onChange={(e) => setStackKey(e.target.value)}>
                {breakdownDims.map((d) => <MenuItem key={d.key} value={d.key}>{dimLabel(d)}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={6} md={2}>
              <TextField select label="Unit" value={unit} fullWidth size="small" disabled={!unitOptions.length}
                helperText={unitOptions.length > 1 ? `${unitOptions.length} units — pick one` : "data unit"}
                onChange={(e) => setUnit(e.target.value)}>
                {unitOptions.map((u) => <MenuItem key={u} value={u}>{u}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={6} md={1}>
              <Button variant="contained" onClick={() => run()} disabled={running} fullWidth>{running ? "…" : "Go"}</Button>
            </Grid>
          </Grid>
          {unitOptions.length > 1 && (
            <Typography variant="caption" color="text.secondary">
              Only values in <b>{unit}</b> are summed — mixing units would be meaningless.
            </Typography>
          )}
        </CardContent>
      </Card>

      {running && <LinearProgress sx={{ mb: 2 }} />}
      {err && <Alert severity="error" sx={{ mb: 2 }}>{err}</Alert>}
      {rows && rows.length === 0 && (
        <Alert severity="warning">No data for this combination{unit ? <> in <b>{unit}</b></> : null}. Try a preset or another unit.</Alert>
      )}
      {option && (
        <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 1 }}>
          <TextField select size="small" label="Chart style" value={chartType}
            onChange={(e) => setChartType(e.target.value)} sx={{ minWidth: 170 }}>
            <MenuItem value="stacked">Stacked bars (composition)</MenuItem>
            <MenuItem value="grouped">Grouped bars (compare)</MenuItem>
            <MenuItem value="line">Lines (trend)</MenuItem>
          </TextField>
        </Box>
      )}
      {option && <ReactECharts option={option} style={{ height: 440 }} notMerge />}

      {/* group definitions */}
      {stackValues.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>What each “{dimLabel(stackDimObj)}” means (ontology / TS):</Typography>
          <Grid container spacing={1}>
            {stackValues.map((s, i) => {
              const info = s.fullIri ? terms[s.fullIri] : null;
              return (
                <Grid item xs={12} sm={6} md={4} key={i}>
                  <Card variant="outlined" sx={{ height: "100%", borderLeft: `4px solid ${PALETTE[i % PALETTE.length]}` }}>
                    <CardContent sx={{ py: 1.5 }}>
                      <Typography variant="subtitle2">{info?.label || s.label}</Typography>
                      <Typography variant="caption" color="text.secondary">{info?.description || "…"}</Typography>
                      {s.fullIri && <Box sx={{ mt: 0.5 }}><Link href={s.fullIri} target="_blank" variant="caption">ontology term ↗</Link></Box>}
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </Box>
      )}

      {/* HOW IT WORKS */}
      <Accordion sx={{ mt: 2 }} disableGutters>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle2">How this works — from raw values to ontology terms</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="info" sx={{ mb: 2 }}>
            Dimensions, predicates and value IRIs come from <code>/oekg/registry/</code>; labels and
            definitions are loaded from the TIB Terminology Service. Works for any annotated table.
          </Alert>
          {rawString ? (
            <>
              <Typography variant="body2" color="text.secondary">Example: one opaque <code>iamc_full_string</code> value —</Typography>
              <Box sx={{ fontFamily: "monospace", my: 1, p: 1, bgcolor: "grey.100", borderRadius: 1 }}>{rawString}</Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>…decomposed into ontology terms (hover for definition, click to open):</Typography>
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                {segments.map(({ seg, match }, i) => (
                  <Box key={i} sx={{ textAlign: "center" }}>
                    <Typography variant="caption" display="block" color="text.secondary">{match ? titleCase(match.dimension) : "unmapped"}</Typography>
                    {match && match.iri
                      ? <TermChip info={terms[match.iri]} fallbackLabel={match.label || seg} fullIri={expandCurie(registry, match.iri)} color={PALETTE[i % PALETTE.length]} />
                      : <Chip label={seg} size="small" variant="outlined" />}
                  </Box>
                ))}
              </Box>
            </>
          ) : (
            <Typography variant="body2" color="text.secondary">
              This dataset has no packed IAMC string; its dimensions come directly from annotated columns.
            </Typography>
          )}
          {lastQuery && (
            <details style={{ marginTop: 16 }}>
              <summary>SPARQL (what ran under the hood)</summary>
              <pre style={{ whiteSpace: "pre-wrap", fontSize: 12 }}>{lastQuery}</pre>
            </details>
          )}
        </AccordionDetails>
      </Accordion>
    </Box>
  );
}
