// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// PROTOTYPE (wayfinder WF-07) — Variant A "Source gallery": browse-first.
// The free-text table field becomes a metadata-rich card gallery (title,
// description, keywords, badges) grouped by dataset family; the analysis
// controls sit below the gallery, chart at the bottom. Closest in spirit to
// today's layout — the cards simply replace the TextField.

import React from "react";
import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import Button from "@mui/material/Button";
import LinearProgress from "@mui/material/LinearProgress";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import {
  UnmappedBadge,
  GranularityChip,
  GranularityLadder,
  VerdictPanel,
  MergedChart,
  ChartTypeSelect,
  NoDataAlert,
  titleCase,
} from "./shared.jsx";

export const VARIANT_NAME = "Source gallery (browse-first)";

export default function VariantA({ ms }) {
  if (!ms.catalog) return <LinearProgress />;
  const families = [...new Set(ms.catalog.map((c) => c.family))];

  return (
    <Box>
      {/* SOURCE GALLERY */}
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        Pick one or more data sources — source becomes a dimension of the
        comparison:
      </Typography>
      {families.map((fam) => (
        <Box key={fam} sx={{ mb: 2 }}>
          <Typography variant="overline" color="text.secondary">
            {fam}
          </Typography>
          <Grid container spacing={1.5}>
            {ms.catalog
              .filter((c) => c.family === fam)
              .map((c) => {
                const on = ms.selected.includes(c.table);
                return (
                  <Grid item xs={12} sm={6} md={4} key={c.table}>
                    <Card
                      variant="outlined"
                      sx={{
                        height: "100%",
                        borderColor: on ? "primary.main" : undefined,
                        borderWidth: on ? 2 : 1,
                        bgcolor: on ? "action.selected" : undefined,
                      }}
                    >
                      <CardActionArea
                        onClick={() => ms.toggle(c.table)}
                        sx={{ height: "100%" }}
                      >
                        <CardContent sx={{ py: 1.5 }}>
                          <Stack
                            direction="row"
                            alignItems="center"
                            spacing={1}
                          >
                            {on && (
                              <CheckCircleIcon
                                color="primary"
                                fontSize="small"
                              />
                            )}
                            <Typography
                              variant="subtitle2"
                              noWrap
                              title={c.title}
                            >
                              {c.title}
                            </Typography>
                          </Stack>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            display="block"
                            sx={{
                              overflow: "hidden",
                              display: "-webkit-box",
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: "vertical",
                              minHeight: 32,
                            }}
                          >
                            {c.description || c.table}
                          </Typography>
                          <Stack
                            direction="row"
                            spacing={0.5}
                            useFlexGap
                            flexWrap="wrap"
                            sx={{ mt: 0.5 }}
                          >
                            <GranularityChip granularity={c.granularity} />
                            <UnmappedBadge unmapped={c.unmapped} />
                            {c.keywords.slice(0, 3).map((k) => (
                              <Chip
                                key={k}
                                size="small"
                                variant="outlined"
                                label={k}
                              />
                            ))}
                          </Stack>
                        </CardContent>
                      </CardActionArea>
                    </Card>
                  </Grid>
                );
              })}
          </Grid>
        </Box>
      ))}

      {/* CONTROLS */}
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="body1" sx={{ mb: 1.5 }}>
            Compare <b>{ms.measure?.label || "…"}</b>
            {ms.unit ? (
              <>
                {" "}
                in <b>{ms.unit}</b>
              </>
            ) : null}{" "}
            per <b>{ms.granularity}</b>, grouped by{" "}
            <b>
              {titleCase(ms.groupKey === "source" ? "source" : ms.groupKey)}
            </b>{" "}
            across <b>{ms.selected.length}</b> source
            {ms.selected.length !== 1 ? "s" : ""}.
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <TextField
                select
                fullWidth
                size="small"
                label="Measure (what to compare)"
                value={ms.measureId}
                onChange={(e) => ms.setMeasureId(e.target.value)}
                helperText="union over the selected sources"
              >
                {ms.measureOptions.map((o) => (
                  <MenuItem
                    key={`${o.space}:${o.value}`}
                    value={`${o.space}:${o.value}`}
                  >
                    {o.label} · {o.selectedProviders}/{ms.selected.length}{" "}
                    selected sources
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={6} md={2}>
              <TextField
                select
                fullWidth
                size="small"
                label="Unit"
                value={ms.unit}
                disabled={!ms.unitOptions.length}
                onChange={(e) => ms.setUnit(e.target.value)}
                helperText="spans all selected sources"
              >
                {ms.unitOptions.map((u) => (
                  <MenuItem key={u} value={u}>
                    {u}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={6} md={3}>
              <GranularityLadder
                ladder={ms.ladder}
                granularity={ms.granularity}
                setGranularity={ms.setGranularity}
              />
            </Grid>
            <Grid item xs={6} md={2}>
              <TextField
                select
                fullWidth
                size="small"
                label="Grouped by"
                value={ms.groupKey}
                onChange={(e) => ms.setGroupKey(e.target.value)}
              >
                {ms.groupOptions.map((o) => (
                  <MenuItem key={o.key} value={o.key}>
                    {o.label}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={6} md={2}>
              <Button
                variant="contained"
                fullWidth
                disabled={ms.running || ms.verdict?.kind === "blocked"}
                onClick={ms.run}
              >
                {ms.running ? "…" : "Compare"}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* VERDICT / CHART */}
      {ms.running && <LinearProgress sx={{ mb: 2 }} />}
      <VerdictPanel verdict={ms.verdict} />
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
        <>
          <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 1 }}>
            <ChartTypeSelect
              chartType={ms.chartType}
              setChartType={ms.setChartType}
              groupKey={ms.groupKey}
            />
          </Box>
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
        </>
      )}
    </Box>
  );
}
