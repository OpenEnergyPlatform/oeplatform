// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// PROTOTYPE (wayfinder WF-07) — Variant C "Sentence builder": guided,
// contract-forward. The whole comparison is composed as one plain-language
// sentence with dropdown slots; the comparability verdict is a LIVE line of
// narrative directly under the sentence — the user reads WHY something merges,
// aggregates or blocks before ever running it. Users learn the contract by
// composing sentences.

import React from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import ListItemText from "@mui/material/ListItemText";
import Checkbox from "@mui/material/Checkbox";
import Button from "@mui/material/Button";
import LinearProgress from "@mui/material/LinearProgress";
import {
  UnmappedBadge,
  GranularityChip,
  MergedChart,
  ChartTypeSelect,
  NoDataAlert,
  titleCase,
} from "./shared.jsx";

export const VARIANT_NAME = "Sentence builder (guided)";

const Slot = ({ children }) => (
  <Box
    component="span"
    sx={{ display: "inline-block", mx: 0.5, verticalAlign: "middle" }}
  >
    {children}
  </Box>
);
const slotSx = {
  fontWeight: 700,
  "& .MuiSelect-select": { py: 0.25 },
  borderBottom: "2px dotted",
  borderColor: "primary.main",
  "&::before, &::after": { display: "none" },
};

export default function VariantC({ ms }) {
  if (!ms.catalog) return <LinearProgress />;
  const titleOf = (t) => ms.catalog.find((c) => c.table === t)?.title || t;

  // the live narrative under the sentence
  const narrative = (() => {
    const v = ms.verdict;
    if (!ms.selected.length)
      return { tone: "info", text: "Pick at least one source." };
    if (!v) return { tone: "info", text: "Pick a measure." };
    if (v.kind === "blocked") {
      return {
        tone: "error",
        text: `⛔ Blocked: ${v.reason} — ${v.detail}${v.pair ? ` (${v.pair.join(" · ")})` : ""}. Nothing is hidden — change a slot and the sentence becomes comparable.`,
      };
    }
    if (v.kind === "aggregate_first") {
      const finer = ms.verdictInput.filter(
        (e) => e.series && e.series.granularity !== ms.granularity
      );
      return {
        tone: "info",
        text: `⟲ Comparable after alignment: ${finer.map((e) => `${titleOf(e.table)} (${e.series.granularity}ly)`).join(", ")} will be ${ms.measure?.aggregation === "mean" ? "averaged" : "summed"} to ${ms.granularity} — the aggregation function comes from the registry, not the chart.`,
      };
    }
    return {
      tone: "success",
      text: "✓ These sources merge: same measure, same unit, same granularity.",
    };
  })();

  return (
    <Box>
      {/* THE SENTENCE */}
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Typography
            component="div"
            variant="h6"
            sx={{ lineHeight: 2.4, fontWeight: 400 }}
          >
            Compare
            <Slot>
              <Select
                multiple
                variant="standard"
                size="small"
                sx={slotSx}
                value={ms.selected}
                onChange={(e) => {
                  const val = e.target.value;
                  const next = typeof val === "string" ? val.split(",") : val;
                  // apply toggles through ms.toggle so shared state stays the boss
                  for (const t of next.filter((t) => !ms.selected.includes(t)))
                    ms.toggle(t);
                  for (const t of ms.selected.filter((t) => !next.includes(t)))
                    ms.toggle(t);
                }}
                renderValue={(sel) =>
                  sel.length === 1 ? titleOf(sel[0]) : `${sel.length} sources`
                }
              >
                {ms.catalog.map((c) => (
                  <MenuItem key={c.table} value={c.table} dense>
                    <Checkbox
                      size="small"
                      checked={ms.selected.includes(c.table)}
                    />
                    <ListItemText
                      primary={
                        <Stack
                          direction="row"
                          spacing={0.5}
                          alignItems="center"
                        >
                          <span>{c.title}</span>
                          <GranularityChip granularity={c.granularity} />
                          <UnmappedBadge unmapped={c.unmapped} />
                        </Stack>
                      }
                      secondary={`${c.family} · ${c.table}`}
                    />
                  </MenuItem>
                ))}
              </Select>
            </Slot>
            on
            <Slot>
              <Select
                variant="standard"
                size="small"
                sx={slotSx}
                value={ms.measureId}
                onChange={(e) => ms.setMeasureId(e.target.value)}
                displayEmpty
                renderValue={(v) => (v ? ms.measure?.label || v : "…")}
              >
                {ms.measureOptions.map((o) => (
                  <MenuItem
                    key={`${o.space}:${o.value}`}
                    value={`${o.space}:${o.value}`}
                  >
                    <ListItemText
                      primary={o.label}
                      secondary={`${o.space} · in ${o.selectedProviders}/${ms.selected.length} selected sources (${o.providers.length} total)`}
                    />
                  </MenuItem>
                ))}
              </Select>
            </Slot>
            {ms.unitOptions.length > 0 && (
              <>
                in
                <Slot>
                  <Select
                    variant="standard"
                    size="small"
                    sx={slotSx}
                    value={ms.unit}
                    onChange={(e) => ms.setUnit(e.target.value)}
                  >
                    {ms.unitOptions.map((u) => (
                      <MenuItem key={u} value={u}>
                        {u}
                      </MenuItem>
                    ))}
                  </Select>
                </Slot>
              </>
            )}
            per
            <Slot>
              <Select
                variant="standard"
                size="small"
                sx={slotSx}
                value={ms.granularity}
                onChange={(e) => ms.setGranularity(e.target.value)}
              >
                {ms.ladder
                  .filter((l) => l.enabled)
                  .map((l) => (
                    <MenuItem key={l.level} value={l.level}>
                      {l.level}
                    </MenuItem>
                  ))}
              </Select>
            </Slot>
            , grouped by
            <Slot>
              <Select
                variant="standard"
                size="small"
                sx={slotSx}
                value={ms.groupKey}
                onChange={(e) => ms.setGroupKey(e.target.value)}
              >
                {ms.groupOptions.map((o) => (
                  <MenuItem key={o.key} value={o.key}>
                    {o.label}
                  </MenuItem>
                ))}
              </Select>
            </Slot>
            .
          </Typography>

          {/* LIVE VERDICT NARRATIVE */}
          <Typography
            variant="body2"
            sx={{ mt: 1 }}
            color={
              narrative.tone === "error"
                ? "error.main"
                : narrative.tone === "success"
                  ? "success.main"
                  : "text.secondary"
            }
          >
            {narrative.text}
          </Typography>

          <Stack direction="row" spacing={1} sx={{ mt: 2 }} alignItems="center">
            <Button
              variant="contained"
              disabled={
                ms.running ||
                ms.verdict?.kind === "blocked" ||
                !ms.selected.length
              }
              onClick={ms.run}
            >
              {ms.running ? "…" : "Run the sentence"}
            </Button>
            <ChartTypeSelect
              chartType={ms.chartType}
              setChartType={ms.setChartType}
              groupKey={ms.groupKey}
            />
            {ms.selected.length > 1 && ms.groupKey === "source" && (
              <Chip
                size="small"
                variant="outlined"
                label="source is the comparison dimension"
              />
            )}
          </Stack>
        </CardContent>
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
        />
      )}
      {ms.verdict?.kind !== "blocked" && !ms.rows && !ms.running && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ textAlign: "center", mt: 4 }}
        >
          The sentence above IS the query — run it to see the merged chart.
        </Typography>
      )}
      <Typography
        variant="caption"
        color="text.secondary"
        display="block"
        sx={{ mt: 2 }}
      >
        What each part of the sentence means: <i>sources</i> come from the VKG
        mapping; the <i>measure</i> is a declared substance or IAMC quantity;
        the <i>unit</i> filter spans all sources; the <i>per</i>-granularity is
        the WF-06 ladder (week needs WEEK() support — coming); grouping by{" "}
        <i>source</i> keeps cross-source values side by side, never summed
        together.
      </Typography>
    </Box>
  );
}
