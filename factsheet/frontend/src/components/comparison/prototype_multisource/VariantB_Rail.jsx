// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// PROTOTYPE (wayfinder WF-07) — Variant B "Workbench rail": comparison-first.
// A persistent left rail holds the source catalog (searchable, compact
// checkbox rows grouped by family, mini-badges); the right side is dominated
// by the chart with a slim toolbar and a COMPARABILITY STRIP above it — the
// verdict is always visible while composing, before anything runs.

import React, { useMemo, useState } from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Typography from "@mui/material/Typography";
import Checkbox from "@mui/material/Checkbox";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import Tooltip from "@mui/material/Tooltip";
import LinearProgress from "@mui/material/LinearProgress";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Autocomplete, { createFilterOptions } from "@mui/material/Autocomplete";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import {
  GranularityLadder,
  VerdictPanel,
  VerdictChip,
  MergedChart,
  ChartTypeSelect,
  CandidateDot,
  NoDataAlert,
  TablePeek,
  PALETTE,
} from "./shared.jsx";

export const VARIANT_NAME = "Workbench rail (comparison-first)";

const measureFilter = createFilterOptions({
  stringify: (o) => `${o.label} ${o.value} ${o.space}`,
});

export default function VariantB({ ms }) {
  const [filter, setFilter] = useState("");
  const [verdictOpen, setVerdictOpen] = useState(false);
  // measure picker controls (reaction round 6): search, sort, and a summary
  // of single-source measures instead of flooding the list with them
  const [measureSort, setMeasureSort] = useState("sources");
  const [includeSingle, setIncludeSingle] = useState(false);
  const singleCount = useMemo(
    () => ms.measureOptions.filter((o) => o.providers.length === 1).length,
    [ms.measureOptions]
  );
  const measureChoices = useMemo(() => {
    // default pool: measures ≥2 sources can compare — plus the current
    // choice, so the field never holds a value missing from its own list
    const pool = includeSingle
      ? ms.measureOptions
      : ms.measureOptions.filter(
          (o) =>
            o.providers.length > 1 ||
            (ms.measure &&
              o.space === ms.measure.space &&
              o.value === ms.measure.value)
        );
    const byLabel = (a, b) => a.label.localeCompare(b.label);
    const sorted = [...pool].sort(
      measureSort === "alpha"
        ? byLabel
        : (a, b) => b.providers.length - a.providers.length || byLabel(a, b)
    );
    // keep multi-provider options ahead of single-provider ones so the
    // Autocomplete group headers appear once each
    return [
      ...sorted.filter((o) => o.providers.length > 1),
      ...sorted.filter((o) => o.providers.length === 1),
    ];
  }, [ms.measureOptions, ms.measure, includeSingle, measureSort]);
  if (!ms.catalog) return <LinearProgress />;

  const visible = ms.catalog.filter(
    (c) =>
      !filter ||
      c.table.toLowerCase().includes(filter.toLowerCase()) ||
      c.title.toLowerCase().includes(filter.toLowerCase()) ||
      c.keywords.some((k) => k.toLowerCase().includes(filter.toLowerCase()))
  );
  const families = [...new Set(visible.map((c) => c.family))];

  return (
    <Box sx={{ display: "flex", gap: 2, alignItems: "flex-start" }}>
      {/* SOURCE RAIL */}
      <Card
        variant="outlined"
        sx={{
          width: 340,
          flexShrink: 0,
          maxHeight: "calc(100vh - 230px)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Box sx={{ p: 1.5, pb: 1 }}>
          <Typography variant="subtitle2" gutterBottom>
            Data sources
            <Typography
              component="span"
              variant="caption"
              color="text.secondary"
              sx={{ ml: 1 }}
            >
              (scenario grouping follows WF-14)
            </Typography>
          </Typography>
          <TextField
            fullWidth
            size="small"
            placeholder="search title, name, keywords…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </Box>
        <Divider />
        <Box sx={{ overflowY: "auto", flex: 1 }}>
          {families.map((fam) => (
            <Box key={fam}>
              <Typography
                variant="overline"
                color="text.secondary"
                sx={{ px: 1.5 }}
              >
                {fam}
              </Typography>
              <List dense disablePadding>
                {visible
                  .filter((c) => c.family === fam)
                  .map((c) => {
                    const on = ms.selected.includes(c.table);
                    return (
                      <ListItemButton
                        key={c.table}
                        dense
                        selected={on}
                        onClick={() => ms.toggle(c.table)}
                      >
                        <Checkbox
                          edge="start"
                          size="small"
                          checked={on}
                          tabIndex={-1}
                          disableRipple
                        />
                        <ListItemText
                          primary={
                            <Stack
                              direction="row"
                              spacing={0.5}
                              alignItems="center"
                            >
                              <CandidateDot status={ms.candidates[c.table]} />
                              <Typography
                                variant="body2"
                                noWrap
                                title={c.title}
                                sx={{ maxWidth: 140 }}
                              >
                                {c.title}
                              </Typography>
                              {c.unmapped.length > 0 && (
                                <Tooltip
                                  arrow
                                  title={c.unmapped
                                    .map((u) => `${u.column} — ${u.reason}`)
                                    .join(" · ")}
                                >
                                  <WarningAmberIcon
                                    color="warning"
                                    sx={{ fontSize: 16 }}
                                  />
                                </Tooltip>
                              )}
                              <TablePeek table={c.table} title={c.title} />
                            </Stack>
                          }
                          secondary={`${c.granularity ? (c.granularity === "hour" ? "hourly" : "yearly") : "no temporal declaration"} · ${c.table}`}
                          secondaryTypographyProps={{
                            noWrap: true,
                            fontSize: 11,
                          }}
                        />
                      </ListItemButton>
                    );
                  })}
              </List>
            </Box>
          ))}
        </Box>
        <Divider />
        <Box sx={{ p: 1.5 }}>
          <Typography variant="caption" color="text.secondary" display="block">
            {ms.selected.length} source{ms.selected.length !== 1 ? "s" : ""}{" "}
            selected
            {ms.selected.length > 1 ? " — grouped by source by default" : ""}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            For <b>{ms.measure?.label || "…"}</b>:{" "}
            <span style={{ color: "#2e7d32" }}>●</span> merges ·{" "}
            <span style={{ color: "#0288d1" }}>●</span> aggregate first ·{" "}
            <span style={{ color: "#d32f2f" }}>●</span> would block ·{" "}
            <span style={{ color: "#9e9e9e" }}>●</span> no data — from the
            registry contract, not heuristics
          </Typography>
        </Box>
      </Card>

      {/* WORKBENCH */}
      <Box sx={{ flex: 1, minWidth: 0 }}>
        {/* MEASURE BAR — the initially required choice sits on top of the
            graph filters (reaction round 2): pick a measure, see how many
            sources from which scenario provide it, select them all at once */}
        <Card variant="outlined" sx={{ px: 1.5, py: 1, mb: 1.5 }}>
          <Stack
            direction="row"
            spacing={2}
            useFlexGap
            flexWrap="wrap"
            alignItems="center"
          >
            <Autocomplete
              size="small"
              sx={{ minWidth: 460 }}
              options={measureChoices}
              filterOptions={measureFilter}
              value={ms.measure}
              onChange={(e, o) => o && ms.setMeasureId(`${o.space}:${o.value}`)}
              disableClearable
              getOptionLabel={(o) => o.label || ""}
              isOptionEqualToValue={(o, v) =>
                o.space === v.space && o.value === v.value
              }
              groupBy={(o) =>
                o.providers.length > 1
                  ? "Comparable across sources"
                  : "Single source only"
              }
              renderOption={(props, o) => (
                <li {...props} key={`${o.space}:${o.value}`}>
                  <ListItemText
                    primary={o.label}
                    secondary={`${o.space === "substance" ? "substance" : "IAMC quantity"} · ${o.providers.length} source${o.providers.length !== 1 ? "s" : ""} provide${o.providers.length === 1 ? "s" : ""} it${o.selectedProviders ? ` (${o.selectedProviders} selected)` : ""}`}
                  />
                </li>
              )}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Measure (start here)"
                  placeholder="search measures…"
                />
              )}
            />
            <ToggleButtonGroup
              exclusive
              size="small"
              value={measureSort}
              onChange={(e, v) => v && setMeasureSort(v)}
            >
              <Tooltip arrow title="Most sources first">
                <ToggleButton value="sources">sources</ToggleButton>
              </Tooltip>
              <Tooltip arrow title="Alphabetical">
                <ToggleButton value="alpha">A–Z</ToggleButton>
              </Tooltip>
            </ToggleButtonGroup>
            {ms.measure && (
              <Typography variant="body2" color="text.secondary">
                Provided by <b>{ms.measure.providers.length}</b> source
                {ms.measure.providers.length !== 1 ? "s" : ""}:{" "}
                {Object.entries(
                  ms.measure.providers.reduce((acc, t) => {
                    const fam =
                      ms.catalog.find((c) => c.table === t)?.family || "other";
                    acc[fam] = (acc[fam] || 0) + 1;
                    return acc;
                  }, {})
                )
                  .map(([fam, n]) => `${fam} (${n})`)
                  .join(" · ")}{" "}
                — {ms.measure.selectedProviders} of{" "}
                {ms.selected.length || "none"} selected provide it
              </Typography>
            )}
            <Box sx={{ flex: 1 }} />
            {ms.measure && (
              <Button
                size="small"
                variant="outlined"
                disabled={
                  ms.measure.providers.length === 0 ||
                  (ms.measure.selectedProviders ===
                    ms.measure.providers.length &&
                    ms.selected.length === ms.measure.providers.length)
                }
                onClick={() => ms.selectProviders(ms.measure.providers)}
              >
                Select all {ms.measure.providers.length} providers
              </Button>
            )}
          </Stack>
          {singleCount > 0 && (
            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
              sx={{ mt: 0.5 }}
            >
              {includeSingle
                ? `Showing ${singleCount} single-source measures too — each has only one scenario dataset, so there is nothing to compare it against yet. `
                : `${singleCount} more measure${singleCount !== 1 ? "s are" : " is"} summarized away: provided by a single source only, so no second scenario dataset exists for a comparison. `}
              <Typography
                component="button"
                variant="caption"
                onClick={() => setIncludeSingle((v) => !v)}
                sx={{
                  border: "none",
                  background: "none",
                  color: "primary.main",
                  cursor: "pointer",
                  p: 0,
                  textDecoration: "underline",
                }}
              >
                {includeSingle
                  ? "hide them again"
                  : "show and search them anyway"}
              </Typography>
            </Typography>
          )}
        </Card>

        {/* toolbar */}
        <Stack
          direction="row"
          spacing={1.5}
          useFlexGap
          flexWrap="wrap"
          alignItems="center"
          sx={{ mb: 1 }}
        >
          <TextField
            select
            size="small"
            label="Unit"
            value={ms.unit}
            disabled={!ms.unitOptions.length}
            sx={{ minWidth: 110 }}
            onChange={(e) => ms.setUnit(e.target.value)}
          >
            {ms.unitOptions.map((u) => (
              <MenuItem key={u} value={u}>
                {u}
              </MenuItem>
            ))}
          </TextField>
          <GranularityLadder
            ladder={ms.ladder}
            granularity={ms.granularity}
            setGranularity={ms.setGranularity}
          />
          <TextField
            select
            size="small"
            label="Grouped by"
            value={ms.groupKey}
            sx={{ minWidth: 170 }}
            onChange={(e) => ms.setGroupKey(e.target.value)}
            helperText={
              ms.groupOptions.find((o) => o.key === ms.groupKey)?.shared ===
              false
                ? "⚠ not in every selected source"
                : undefined
            }
          >
            {ms.groupOptions.map((o) => (
              <MenuItem key={o.key} value={o.key}>
                {o.label}
                {o.shared === false ? " — some sources only" : ""}
              </MenuItem>
            ))}
          </TextField>
          <ChartTypeSelect
            chartType={ms.chartType}
            setChartType={ms.setChartType}
            groupKey={ms.groupKey}
          />
          <Button
            variant="contained"
            disabled={ms.running || ms.verdict?.kind === "blocked"}
            onClick={ms.run}
          >
            {ms.running ? "…" : "Compare"}
          </Button>
        </Stack>

        {/* COMPARABILITY STRIP — always visible while composing */}
        <Card variant="outlined" sx={{ px: 1.5, py: 1, mb: 1.5 }}>
          <Stack
            direction="row"
            spacing={1}
            useFlexGap
            flexWrap="wrap"
            alignItems="center"
          >
            {ms.selectedEntries.map((c, i) => (
              <Chip
                key={c.table}
                size="small"
                label={c.title}
                sx={{ borderLeft: `4px solid ${PALETTE[i % PALETTE.length]}` }}
                onDelete={() => ms.toggle(c.table)}
              />
            ))}
            <Box sx={{ flex: 1 }} />
            <VerdictChip
              verdict={ms.verdict}
              onClick={() => setVerdictOpen((v) => !v)}
            />
          </Stack>
          {(verdictOpen || ms.verdict?.kind === "blocked") && (
            <Box sx={{ mt: 1 }}>
              <VerdictPanel verdict={ms.verdict} dense />
            </Box>
          )}
        </Card>

        {/* CHART */}
        {ms.running && <LinearProgress sx={{ mb: 2 }} />}
        {ms.err && <Typography color="error">{ms.err}</Typography>}
        {ms.verdict?.kind !== "blocked" && ms.rows && ms.rows.length === 0 && (
          <NoDataAlert
            measure={ms.measure}
            unit={ms.unit}
            granularity={ms.ranGranularity || ms.granularity}
            nSources={ms.selected.length}
          />
        )}
        {ms.verdict?.kind !== "blocked" && ms.rows && ms.rows.length > 0 && (
          <MergedChart
            registry={ms.registry}
            rows={ms.rows}
            groupKey={ms.groupKey}
            unit={ms.unit}
            chartType={ms.chartType}
            granularity={ms.ranGranularity || ms.granularity}
            catalog={ms.catalog}
            notices={ms.notices}
            unmappedFootnotes={ms.unmappedFootnotes}
            stale={ms.stale}
            running={ms.running}
            onRerun={ms.run}
            summary={ms.ranSummary}
          />
        )}
        {!ms.rows && !ms.running && ms.verdict?.kind !== "blocked" && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mt: 4, textAlign: "center" }}
          >
            Compose a comparison on the left, then hit <b>Compare</b>.
          </Typography>
        )}
      </Box>
    </Box>
  );
}
