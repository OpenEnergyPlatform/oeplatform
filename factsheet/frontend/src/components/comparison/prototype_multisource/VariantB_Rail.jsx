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
import Alert from "@mui/material/Alert";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Autocomplete, { createFilterOptions } from "@mui/material/Autocomplete";
import Paper from "@mui/material/Paper";
import InputAdornment from "@mui/material/InputAdornment";
import IconButton from "@mui/material/IconButton";
import Badge from "@mui/material/Badge";
import Collapse from "@mui/material/Collapse";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import SortIcon from "@mui/icons-material/Sort";
import SortByAlphaIcon from "@mui/icons-material/SortByAlpha";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import ViewListIcon from "@mui/icons-material/ViewList";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
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

// round icon-button filter idiom (round 7)
const roundBtn = (on) => ({
  width: 28,
  height: 28,
  border: "1px solid",
  borderColor: on ? "primary.main" : "divider",
  bgcolor: on ? "primary.main" : "transparent",
  color: on ? "primary.contrastText" : "text.secondary",
  "&:hover": { bgcolor: on ? "primary.dark" : "action.hover" },
});

export default function VariantB({ ms }) {
  const [filter, setFilter] = useState("");
  const [verdictOpen, setVerdictOpen] = useState(false);
  // rail mode (round 9): browse tables flat, or lead with the SCENARIO —
  // for now scenario = dataset family; the OEKG scenario bundle becomes the
  // source of definition once WF-14 harvests the links
  const [railMode, setRailMode] = useState("tables");
  const [expandedFams, setExpandedFams] = useState(() => new Set());
  const toggleExpand = (fam) =>
    setExpandedFams((prev) => {
      const n = new Set(prev);
      if (n.has(fam)) n.delete(fam);
      else n.add(fam);
      return n;
    });
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

  // Sort + single-source controls live INSIDE the dropdown, next to the
  // search (reaction round 7) — as small round icon buttons with hover help,
  // the way filter controls are usually shown (round 7 follow-up).
  // onMouseDown preventDefault keeps the input focused so clicking them
  // doesn't close the popup.
  const MeasurePaper = useMemo(() => {
    return function MeasurePaper({ children, ...rest }) {
      return (
        <Paper {...rest}>
          <Stack
            direction="row"
            spacing={0.75}
            alignItems="center"
            onMouseDown={(e) => e.preventDefault()}
            sx={{
              px: 1.5,
              py: 0.75,
              borderBottom: "1px solid",
              borderColor: "divider",
            }}
          >
            <Tooltip arrow title="Sort by number of sources — most first">
              <IconButton
                size="small"
                onClick={() => setMeasureSort("sources")}
                sx={roundBtn(measureSort === "sources")}
              >
                <SortIcon sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>
            <Tooltip arrow title="Sort alphabetically">
              <IconButton
                size="small"
                onClick={() => setMeasureSort("alpha")}
                sx={roundBtn(measureSort === "alpha")}
              >
                <SortByAlphaIcon sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>
            <Box sx={{ flex: 1 }} />
            {singleCount > 0 && (
              <Tooltip
                arrow
                title={
                  includeSingle
                    ? "Hide single-source measures again"
                    : `Show ${singleCount} hidden measure${singleCount !== 1 ? "s" : ""} provided by a single source only — no second scenario dataset exists to compare them against`
                }
              >
                <Badge
                  badgeContent={includeSingle ? 0 : singleCount}
                  color="primary"
                  overlap="circular"
                >
                  <IconButton
                    size="small"
                    onClick={() => setIncludeSingle((v) => !v)}
                    sx={roundBtn(includeSingle)}
                  >
                    {includeSingle ? (
                      <VisibilityIcon sx={{ fontSize: 16 }} />
                    ) : (
                      <VisibilityOffIcon sx={{ fontSize: 16 }} />
                    )}
                  </IconButton>
                </Badge>
              </Tooltip>
            )}
          </Stack>
          {children}
        </Paper>
      );
    };
  }, [measureSort, includeSingle, singleCount]);
  if (!ms.catalog) return <LinearProgress />;

  // round 10: measures per rail row + scenario provenance per measure option
  const measuresOf = (table) =>
    ms.measureOptions.filter((o) => o.providers.includes(table));
  const famBreakdown = (o) => {
    const counts = {};
    for (const t of o.providers) {
      const f = ms.catalog.find((c) => c.table === t)?.family || "other";
      counts[f] = (counts[f] || 0) + 1;
    }
    return Object.entries(counts)
      .map(([f, n]) => `${f} (${n})`)
      .join(" · ");
  };

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
          <Stack direction="row" alignItems="center" sx={{ mb: 0.5 }}>
            <Typography variant="subtitle2" sx={{ flex: 1 }}>
              Data sources
            </Typography>
            <Tooltip arrow title="Browse individual tables">
              <IconButton
                size="small"
                onClick={() => setRailMode("tables")}
                sx={{ ...roundBtn(railMode === "tables"), mr: 0.5 }}
              >
                <ViewListIcon sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>
            <Tooltip
              arrow
              title="Select by scenario — one tick takes the whole scenario dataset (scenario = dataset family for now; the OEKG scenario bundle becomes the source of definition with WF-14)"
            >
              <IconButton
                size="small"
                onClick={() => setRailMode("scenarios")}
                sx={roundBtn(railMode === "scenarios")}
              >
                <AccountTreeIcon sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>
          </Stack>
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
          {families.map((fam) => {
            const famTables = ms.catalog
              .filter((c) => c.family === fam)
              .map((c) => c.table);
            const selCount = famTables.filter((t) =>
              ms.selected.includes(t)
            ).length;
            const open = railMode === "tables" || expandedFams.has(fam);
            return (
              <Box key={fam}>
                {/* scenario row (round 9): one tick selects the whole dataset
                  family — the scenario stand-in until WF-14 */}
                <Stack direction="row" alignItems="center" sx={{ pr: 0.5 }}>
                  <Checkbox
                    size="small"
                    checked={selCount === famTables.length}
                    indeterminate={selCount > 0 && selCount < famTables.length}
                    onChange={(e) =>
                      ms.toggleFamily(famTables, e.target.checked)
                    }
                  />
                  <Typography
                    variant="overline"
                    color="text.secondary"
                    noWrap
                    sx={{
                      flex: 1,
                      cursor: railMode === "scenarios" ? "pointer" : undefined,
                    }}
                    onClick={
                      railMode === "scenarios"
                        ? () => toggleExpand(fam)
                        : undefined
                    }
                  >
                    {fam} ({selCount}/{famTables.length})
                  </Typography>
                  {railMode === "scenarios" && (
                    <IconButton size="small" onClick={() => toggleExpand(fam)}>
                      {open ? (
                        <ExpandLessIcon sx={{ fontSize: 18 }} />
                      ) : (
                        <ExpandMoreIcon sx={{ fontSize: 18 }} />
                      )}
                    </IconButton>
                  )}
                </Stack>
                <Collapse in={open}>
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
                                  <CandidateDot
                                    status={ms.candidates[c.table]}
                                  />
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
                              secondary={
                                <>
                                  <span
                                    style={{
                                      display: "block",
                                      whiteSpace: "nowrap",
                                      overflow: "hidden",
                                      textOverflow: "ellipsis",
                                    }}
                                  >
                                    {c.granularity
                                      ? c.granularity === "hour"
                                        ? "hourly"
                                        : "yearly"
                                      : "no temporal declaration"}{" "}
                                    · {c.table}
                                  </span>
                                  {/* measures this table provides (round 10);
                                      the chosen one is bolded */}
                                  <span
                                    style={{
                                      display: "block",
                                      whiteSpace: "nowrap",
                                      overflow: "hidden",
                                      textOverflow: "ellipsis",
                                    }}
                                    title={measuresOf(c.table)
                                      .map((o) => o.label)
                                      .join(" · ")}
                                  >
                                    {measuresOf(c.table).length
                                      ? measuresOf(c.table).map((o, i) => (
                                          <React.Fragment
                                            key={`${o.space}:${o.value}`}
                                          >
                                            {i > 0 && " · "}
                                            {ms.measure &&
                                            o.space === ms.measure.space &&
                                            o.value === ms.measure.value ? (
                                              <b>{o.label}</b>
                                            ) : (
                                              o.label
                                            )}
                                          </React.Fragment>
                                        ))
                                      : "no measures declared"}
                                  </span>
                                </>
                              }
                              secondaryTypographyProps={{
                                component: "div",
                                fontSize: 11,
                              }}
                            />
                          </ListItemButton>
                        );
                      })}
                  </List>
                </Collapse>
              </Box>
            );
          })}
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
              PaperComponent={MeasurePaper}
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
                    secondary={
                      <>
                        <span style={{ display: "block" }}>
                          {o.space === "substance"
                            ? "substance"
                            : "IAMC quantity"}{" "}
                          · {o.providers.length} source
                          {o.providers.length !== 1 ? "s" : ""} provide
                          {o.providers.length === 1 ? "s" : ""} it
                          {o.selectedProviders
                            ? ` (${o.selectedProviders} selected)`
                            : ""}
                        </span>
                        {/* scenario provenance (round 10): which scenario(s)
                            the providing sources belong to */}
                        <span style={{ display: "block" }}>
                          from {famBreakdown(o)}
                        </span>
                      </>
                    }
                    secondaryTypographyProps={{ component: "div" }}
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
            InputProps={
              ms.groupOptions.find((o) => o.key === ms.groupKey)?.shared ===
              false
                ? {
                    startAdornment: (
                      <InputAdornment position="start">
                        <Tooltip
                          arrow
                          title="This dimension is not present in every selected source — sources lacking it drop out of the chart."
                        >
                          <WarningAmberIcon
                            color="warning"
                            sx={{ fontSize: 18 }}
                          />
                        </Tooltip>
                      </InputAdornment>
                    ),
                  }
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
          {/* facet filters (round 9): a spread facet can be pinned to one
              value instead of grouped by — "everything summed all the time"
              stops being the only alternative */}
          {Object.entries(ms.facetSpread)
            .filter(([, vals]) => vals.length > 1)
            .map(([key, vals]) => (
              <TextField
                key={key}
                select
                size="small"
                label={key.replace(/_/g, " ")}
                value={ms.facetFilters[key] || "all"}
                sx={{ minWidth: 165 }}
                onChange={(e) => ms.setFacetFilter(key, e.target.value)}
              >
                <MenuItem value="all">all (summed)</MenuItem>
                {vals.map((v) => (
                  <MenuItem key={v.iri} value={v.iri}>
                    {v.label}
                  </MenuItem>
                ))}
                <MenuItem value="none">without this facet</MenuItem>
              </TextField>
            ))}
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

        {/* FACET-CONFLATION GUARD (round 8): the meaning of a value is the
            combination of its annotations — never sum bid+award style facets
            into one series without saying so */}
        {ms.conflations.map((c) => (
          <Alert
            key={c.key}
            severity="warning"
            sx={{ mb: 1.5 }}
            action={
              <Button
                size="small"
                color="warning"
                variant="outlined"
                onClick={() => ms.setGroupKey(c.key)}
              >
                Group by {c.label}
              </Button>
            }
          >
            The selected sources annotate <b>{ms.measure?.label}</b> values with
            several <b>{c.label}</b> facets ({c.values.join(" · ")}). Grouped by{" "}
            {ms.groupKey === "source" ? "source" : ms.groupKey}, these different
            things are <b>summed into one series</b> — group by {c.label}, or
            pin one value with the {c.label.toLowerCase()} filter in the
            toolbar.
          </Alert>
        ))}

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
