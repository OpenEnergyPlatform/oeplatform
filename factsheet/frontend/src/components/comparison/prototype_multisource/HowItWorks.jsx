// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// PROTOTYPE (wayfinder WF-07, reaction round 6) — content for the previously
// dead "How it works?" button on the comparison board. Explains each tab in
// user language; the Registry section walks through the semantic-layer flow
// the workbench is built on, so users understand WHY something merges,
// aggregates or blocks — nothing here is decoration, every claim mirrors an
// implemented rule.

import React from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";

const Step = ({ n, title, children }) => (
  <Box sx={{ mb: 2 }}>
    <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
      {n}. {title}
    </Typography>
    <Typography variant="body2" color="text.secondary">
      {children}
    </Typography>
  </Box>
);

function RegistryContent() {
  return (
    <>
      <Typography variant="body2" sx={{ mb: 2 }}>
        The Registry (beta) view compares{" "}
        <b>quantitative data across data sources</b> — different scenarios,
        models and reporting datasets — and only ever merges what the data
        itself declares comparable. Everything you see is driven by the
        platform&apos;s semantic layer (the table annotations published with
        each dataset), not by hand-maintained configuration.
      </Typography>
      <Step n={1} title="Data sources (left rail)">
        Every table whose annotations are mapped into the knowledge graph
        appears here automatically — publishing a well-annotated table is all it
        takes to show up. The colored dot in front of each source tells you what
        would happen if you added it to your current selection: green merges
        directly, blue is comparable after aggregation to a common time
        resolution, red would block the comparison (the tooltip names the exact
        reason), grey holds no data for the chosen measure. A warning triangle
        means some columns of that table could not be annotated — values from
        those columns may be missing. The eye icon shows the first raw rows so
        you can inspect what is actually in a table.
      </Step>
      <Step n={2} title="Measure — what to compare (start here)">
        A measure is what the values mean: an ontology-annotated substance (e.g.
        electricity price, CO2 emission) or an IAMC-style variable. The picker
        shows how many sources provide each measure and from which scenario
        families; measures held by only one source are summarized away by
        default, because a single scenario dataset has nothing to be compared
        against. &quot;Select all providers&quot; pulls every source that
        reports the measure into the selection at once. Substance-based and
        IAMC-based measures are separate vocabularies and are never mixed
        silently.
      </Step>
      <Step n={3} title="The comparability verdict">
        Before anything runs, the tool checks every pair of selected sources
        against a fixed contract: same measure, same declared unit, and a
        reachable common time resolution. The result is always one of{" "}
        <b>merge</b> (plotted as stored), <b>aggregate first</b> (finer series
        are rolled up to the coarsest common resolution) or <b>blocked</b> with
        a named reason. A blocked selection stays fully selectable — the chart
        area explains what blocks and which two sources clash, so you can fix
        the selection instead of guessing.
      </Step>
      <Step n={4} title="Time resolution and aggregation">
        The hour / day / month / year ladder offers only resolutions every
        selected source can reach. When rolling up, the aggregation function
        (sum vs. average) comes from the dataset&apos;s own declaration — an
        energy amount is summed, a price is averaged; the chart never chooses.
        Yearly values use the year each dataset declares for its scenario, not a
        year extracted from timestamps.
      </Step>
      <Step n={5} title="The chart">
        All sources land in one merged result; <b>source</b> is a dimension like
        any other and the default grouping when several are selected. Values
        from different sources are never stacked or summed together. The
        generated title states exactly what is plotted, and the line under it
        states whether any calculation was applied to the stored values. Legend
        entries resolve to ontology terms — hover for the definition, click the
        chips under the chart to open the term. Long series can be zoomed with
        the mouse wheel or the range slider.
      </Step>
      <Typography variant="caption" color="text.secondary">
        In short: annotate your data well and it becomes comparable here by
        itself — the view adds no interpretation of its own.
      </Typography>
    </>
  );
}

const CONTENT = {
  Registry: {
    title: "How the Registry (beta) comparison works",
    body: <RegistryContent />,
  },
  Qualitative: {
    title: "How the qualitative comparison works",
    body: (
      <Typography variant="body2" color="text.secondary">
        The qualitative view compares the <b>scenario bundles</b> you selected
        on the listing page: study context, scenario descriptions, interacting
        regions, input and output datasets, and the other facts recorded in the
        Open Energy Knowledge Graph. It puts the bundles side by side so
        differences in scope and assumptions are visible before any numbers are
        compared — use it to judge whether two scenarios are about the same
        question at all.
      </Typography>
    ),
  },
  Quantitative: {
    title: "How the quantitative comparison works",
    body: (
      <Typography variant="body2" color="text.secondary">
        The quantitative view charts data of the selected scenarios&apos; linked
        tables. It predates the Registry (beta) view and works per table; the
        Registry tab is its successor and adds multi-source selection with
        declared-comparability checking.
      </Typography>
    ),
  },
};

export default function HowItWorksDialog({ open, onClose, alignment }) {
  const c = CONTENT[alignment] || CONTENT.Registry;
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{c.title}</DialogTitle>
      <Divider />
      <DialogContent>{c.body}</DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
