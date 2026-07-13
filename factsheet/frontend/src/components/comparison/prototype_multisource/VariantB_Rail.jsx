// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// PROTOTYPE (wayfinder WF-07) — Variant B "Workbench rail": comparison-first.
// A persistent left rail holds the source catalog (searchable, compact
// checkbox rows grouped by family, mini-badges); the right side is dominated
// by the chart with a slim toolbar and a COMPARABILITY STRIP above it — the
// verdict is always visible while composing, before anything runs.

import React, { useState } from "react";
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
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import {
  GranularityLadder,
  VerdictPanel,
  VerdictChip,
  MergedChart,
  ChartTypeSelect,
  CandidateDot,
  PALETTE,
} from "./shared.jsx";

export const VARIANT_NAME = "Workbench rail (comparison-first)";

export default function VariantB({ ms }) {
  const [filter, setFilter] = useState("");
  const [verdictOpen, setVerdictOpen] = useState(false);
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
                                sx={{ maxWidth: 160 }}
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
            label="Measure (start here)"
            value={ms.measureId}
            sx={{ minWidth: 260 }}
            onChange={(e) => ms.setMeasureId(e.target.value)}
            helperText={
              ms.measure
                ? `${ms.measure.selectedProviders}/${ms.selected.length} selected sources provide it`
                : "the rail dots show which sources provide it"
            }
          >
            {ms.measureOptions.map((o) => (
              <MenuItem
                key={`${o.space}:${o.value}`}
                value={`${o.space}:${o.value}`}
              >
                <ListItemText
                  primary={o.label}
                  secondary={`${o.space === "substance" ? "substance" : "IAMC quantity"} · ${o.providers.length} source${o.providers.length !== 1 ? "s" : ""} provide${o.providers.length === 1 ? "s" : ""} it${o.selectedProviders ? ` (${o.selectedProviders} selected)` : ""}`}
                />
              </MenuItem>
            ))}
          </TextField>
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
        {ms.verdict?.kind !== "blocked" && ms.rows && (
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
