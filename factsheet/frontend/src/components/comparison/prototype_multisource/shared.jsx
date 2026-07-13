// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// PROTOTYPE (wayfinder WF-07) — shared presentational atoms. The variants
// differ in layout/hierarchy; these atoms keep the decided semantics
// (badge wording, verdict reasons, ladder, chart correctness) identical
// across them so the maintainer reacts to STRUCTURE, not to copy drift.

import React, { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import AlertTitle from "@mui/material/AlertTitle";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import MenuItem from "@mui/material/MenuItem";
import TextField from "@mui/material/TextField";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { labelForIri } from "../registryQuery.js";
import { LADDER } from "../comparability.js";
import { bucketLabel } from "./protoData.js";

export const PALETTE = [
  "#1f77b4",
  "#ff7f0e",
  "#2ca02c",
  "#d62728",
  "#9467bd",
  "#8c564b",
  "#e377c2",
  "#7f7f7f",
  "#bcbd22",
  "#17becf",
];
export const titleCase = (k) =>
  String(k)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

// WF-05 incompleteness badge: registry-reported unmapped columns.
export function UnmappedBadge({ unmapped, size = "small" }) {
  if (!unmapped?.length) return null;
  return (
    <Tooltip
      arrow
      title={
        <Box sx={{ p: 0.5 }}>
          {unmapped.map((u, i) => (
            <Typography key={i} variant="caption" display="block">
              <b>{u.column}</b> — {u.reason}
            </Typography>
          ))}
        </Box>
      }
    >
      <Chip
        icon={<WarningAmberIcon />}
        size={size}
        color="warning"
        variant="outlined"
        label={`${unmapped.length} column${unmapped.length > 1 ? "s" : ""} not comparable`}
      />
    </Tooltip>
  );
}

export function GranularityChip({ granularity }) {
  if (!granularity)
    return (
      <Chip
        size="small"
        variant="outlined"
        color="error"
        label="no temporal declaration"
      />
    );
  return (
    <Chip
      size="small"
      variant="outlined"
      label={granularity === "hour" ? "hourly" : "yearly"}
    />
  );
}

// The WF-06 hour/day/week/month/year ladder. Week stays visible but disabled
// (no WEEK() through ontop; ISO weeks cross month/year bounds).
export function GranularityLadder({
  ladder,
  granularity,
  setGranularity,
  size = "small",
}) {
  return (
    <ToggleButtonGroup
      exclusive
      size={size}
      value={granularity}
      onChange={(e, v) => v && setGranularity(v)}
    >
      {ladder.map((l) => (
        <ToggleButton key={l.level} value={l.level} disabled={!l.enabled}>
          {l.level}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}

// WF-12 decision 4: blocked selections keep everything selectable; the chart
// is REPLACED by a structured reason naming the offending declarations.
export function VerdictPanel({ verdict, dense = false }) {
  if (!verdict) return null;
  if (verdict.kind === "blocked") {
    return (
      <Alert severity="error" icon={false} sx={{ my: dense ? 0 : 2 }}>
        <AlertTitle sx={{ fontWeight: 700 }}>
          Blocked: {verdict.reason}
        </AlertTitle>
        <Typography variant="body2">{verdict.detail}</Typography>
        {verdict.pair && (
          <Typography variant="caption" color="text.secondary">
            offending pair: {verdict.pair.join(" · ")}
          </Typography>
        )}
        <Typography variant="caption" display="block" sx={{ mt: 1 }}>
          Nothing is hidden — adjust the selection or the measure; the contract
          only merges what is declared comparable.
        </Typography>
      </Alert>
    );
  }
  if (verdict.kind === "aggregate_first") {
    return (
      <Alert severity="info" sx={{ my: dense ? 0 : 2 }}>
        Sources report at different granularities — the finer series are
        auto-aligned to the coarsest common rung (<b>{verdict.target}</b>) per
        the registry&apos;s aggregation hint.
      </Alert>
    );
  }
  return null;
}

export function VerdictChip({ verdict, onClick }) {
  if (!verdict) return null;
  const map = {
    merge: { color: "success", label: "✓ comparable — merge" },
    aggregate_first: { color: "info", label: "⟲ comparable — aggregate first" },
    blocked: { color: "error", label: `⛔ blocked: ${verdict.reason}` },
  };
  const m = map[verdict.kind];
  return (
    <Chip size="small" color={m.color} label={m.label} onClick={onClick} />
  );
}

// Rail indicator: what would happen if this table joined the selection —
// computed from the pure contract (reaction round 1, items 2+3).
export function CandidateDot({ status }) {
  if (!status) return null;
  const map = {
    merge: {
      color: "#2e7d32",
      label: "comparable — merges with the selection",
    },
    aggregate_first: {
      color: "#0288d1",
      label: "comparable after aggregation to a common granularity",
    },
    blocked: { color: "#d32f2f", label: `would block: ${status.reason}` },
    no_data: {
      color: "#9e9e9e",
      label: `no data for this measure (${status.reason})`,
    },
  };
  const m = map[status.kind] || map.no_data;
  return (
    <Tooltip
      arrow
      title={`${m.label}${status.detail ? ` — ${status.detail}` : ""}`}
    >
      <Box
        component="span"
        sx={{
          width: 10,
          height: 10,
          borderRadius: "50%",
          bgcolor: m.color,
          display: "inline-block",
          flexShrink: 0,
        }}
      />
    </Tooltip>
  );
}

// One merged chart over the GROUP BY result rows. Source is a first-class
// dimension: grouped by table_name unless another group dim is chosen.
// `stale` dims the chart once parameters diverge from the run (item 4).
export function MergedChart({
  registry,
  rows,
  groupKey,
  unit,
  chartType,
  granularity,
  catalog = [],
  notices = [],
  unmappedFootnotes = [],
  stale = false,
  onRerun = null,
  running = false,
}) {
  const option = useMemo(() => {
    if (!rows || !registry) return null;
    const byKey = Object.fromEntries(
      (registry.dimensions || []).map((d) => [d.key, d])
    );
    const groupDim = groupKey !== "source" ? byKey[groupKey] : null;
    const titleOf = (t) => catalog.find((c) => c.table === t)?.title || t;
    const seriesKey = (r) =>
      groupDim
        ? groupDim.object_kind === "iri"
          ? labelForIri(registry, groupDim, r[groupDim.key]?.value)
          : r[groupDim.key]?.value
        : titleOf(r.table_name?.value);
    const xVals = [
      ...new Set(rows.map((r) => bucketLabel(r, granularity))),
    ].sort();
    const names = [];
    const matrix = {};
    for (const r of rows) {
      const s = seriesKey(r);
      const x = bucketLabel(r, granularity);
      const v = parseFloat(r.value?.value);
      if (s == null || Number.isNaN(v)) continue;
      if (!names.includes(s)) names.push(s);
      matrix[s] = matrix[s] || {};
      matrix[s][x] = (matrix[s][x] || 0) + v;
    }
    const isLine = chartType === "line";
    // WF-02 guardrail mirrored here: never stack when source is the group-by
    const stacked = chartType === "stacked" && groupKey !== "source";
    return {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: isLine ? "line" : "shadow" },
      },
      legend: { type: "scroll", top: 0 },
      grid: { left: 80, right: 20, bottom: 40, top: 40 },
      xAxis: { type: "category", data: xVals, name: titleCase(granularity) },
      yAxis: { type: "value", name: unit || "value" },
      series: names.map((n, i) => ({
        name: n,
        type: isLine ? "line" : "bar",
        ...(stacked ? { stack: "total" } : {}),
        showSymbol: xVals.length < 100,
        smooth: false,
        emphasis: { focus: "series" },
        itemStyle: { color: PALETTE[i % PALETTE.length] },
        data: xVals.map((x) => matrix[n]?.[x] ?? null),
      })),
    };
  }, [rows, registry, groupKey, unit, chartType, granularity, catalog]);

  if (!option) return null;
  return (
    <Box>
      <Box sx={{ position: "relative" }}>
        <Box sx={{ opacity: stale ? 0.3 : 1, transition: "opacity 0.2s" }}>
          <ReactECharts option={option} style={{ height: 420 }} notMerge />
        </Box>
        {stale && (
          <Box
            sx={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Alert
              severity="warning"
              action={
                onRerun && (
                  <Button
                    size="small"
                    variant="contained"
                    color="warning"
                    disabled={running}
                    onClick={onRerun}
                  >
                    {running ? "…" : "Update chart"}
                  </Button>
                )
              }
            >
              Parameters changed — the chart still shows the previous
              configuration.
            </Alert>
          </Box>
        )}
      </Box>
      {(notices.length > 0 || unmappedFootnotes.length > 0) && (
        <Box sx={{ mt: 1 }}>
          {notices.map((n, i) => (
            <Typography
              key={i}
              variant="caption"
              display="block"
              color="text.secondary"
            >
              ⟲ {n}
            </Typography>
          ))}
          {unmappedFootnotes.map((f, i) => (
            <Typography
              key={`u${i}`}
              variant="caption"
              display="block"
              color="text.secondary"
            >
              ⚠ {f.table}: {f.count} column{f.count > 1 ? "s" : ""} not
              comparable — values may be missing (
              {f.details.map((d) => d.column).join(", ")})
            </Typography>
          ))}
        </Box>
      )}
    </Box>
  );
}

// WF-02 guardrail: stacking across sources is never offered while source is
// the group-by — a cross-source stack reads as a sum nobody asked for.
export function ChartTypeSelect({ chartType, setChartType, groupKey, sx }) {
  const stackBlocked = groupKey === "source";
  return (
    <TextField
      select
      size="small"
      label="Chart style"
      value={stackBlocked && chartType === "stacked" ? "grouped" : chartType}
      onChange={(e) => setChartType(e.target.value)}
      sx={{ minWidth: 160, ...sx }}
      helperText={
        stackBlocked ? "stacking is off while grouped by source" : undefined
      }
    >
      <MenuItem value="line">Lines (trend)</MenuItem>
      <MenuItem value="grouped">Grouped bars (compare)</MenuItem>
      <MenuItem value="stacked" disabled={stackBlocked}>
        Stacked bars (composition)
      </MenuItem>
    </TextField>
  );
}

export { LADDER };
