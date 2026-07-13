# PROTOTYPE — Multi-source selection UI (wayfinder WF-07)

**Question:** How should selecting multiple data sources look and behave in the
Registry (beta) view?

**Plan:** Three structurally different variants on the existing Registry (beta)
tab of the comparison route, switchable via `?variant=` (floating bar, dev
builds only). All variants share one state machine (`useMultiSource.js`) — the
selection survives switching — and implement the decided semantics:

- WF-02 — merged result set, _source_ as first-class dimension (default group-by
  when >1 source), unit filter spans all sources, no stacking across sources.
- WF-05 — registry `unmapped_columns` → incompleteness badge on cards + footnote
  on charts.
- WF-06 — hour/day/week/month/year ladder; yearly buckets use the DECLARED
  `scenario_year`, never `EXTRACT(YEAR)`; aggregation function comes from the
  registry's per-substance hint. `week` is visible but disabled (no `WEEK()`
  through ontop; ISO weeks cross month/year bounds).
- WF-12 — pure verdict function in `../comparability.js`
  (`merge | aggregate_first | blocked(reason)`, fixed reason vocabulary);
  blocked selections stay selectable, the chart is replaced by a structured
  reason. **Keep `comparability.js` when deleting this prototype** — it is the
  decided contract, not throwaway.
- WF-13 — the convertible-unit leg is implemented as a seam in
  `comparability.js` (`units` map param); inert until the registry serves
  `units:` entries. String equality is the live guard.

## Run

```bash
python manage.py runserver     # Django on :8000 (registry, rows API, /api/oevkg-query)
./docker/ontop-reload.sh --check   # make sure ontop serves the current mapping
npm run dev                    # vite; open the comparison page → Registry (beta) tab
```

Variants: `?variant=A` gallery (browse-first) · `?variant=B` workbench rail
(comparison-first) · `?variant=C` sentence builder (guided) · `?variant=0`
today's single-source view for contrast. ←/→ keys cycle.

Demo selections against the live test bench:

- `day_ahead_market_single_zone` + `generic_flexibility_trader` +
  `sensitivity_forecaster`, measure _electricity price_ → **merge** (hourly,
  EUR/MWh); ladder to month/year shows the registry `mean` hint at work.
- any AMIRIS table + `ariadne2_data_with_labels` → **blocked: measure spaces not
  aligned** (substance vs quantity_kind — WF-12 decision 1).
- any AMIRIS table + `eu_leg_data_2021_rep_table_1` → **blocked** under the
  prototype assumption below.
- `biogas` + `conventional_plant_operator`, measure _electrical energy_ →
  **merge**, grouped by source; regroup by `transaction_role` for the facet
  view.

## Prototype assumptions to react to (not pinned by prior tickets)

1. **A table with NO measure dimension (eu_leg live) is treated as its own
   measure space** → always blocked against other sources, reason "measure
   spaces not aligned … declares no measure dimension". _Reacted (2026-07-12):_
   the declaration exists in the metadata (value column
   `isAbout OEO_00140082 greenhouse gas emission value`, species per row via
   `gas` valueReferences) but the hand-written eu_leg mapping never emits it and
   the substance enum lacks the concept — charted as wayfinder ticket WF-21.
   Once fixed, this UI picks the measure up automatically (it discovers measures
   from the VKG).
2. **Dataset family grouping on the cards is a frontend heuristic**
   (`familyOf()` prefix match). Should come from the semantic layer (Datasets
   feature / registry) eventually.
3. Sub-year buckets use `YEAR(?ts)/MONTH(?ts)/DAY(?ts)` on `time_step` — the
   WF-06 bookings-in-period caveat is shown as a chart footnote whenever
   day/month granularity includes an AMIRIS source.
4. When a table reports several units for the chosen measure (per-row-unit
   tables), the chosen unit filters rows (WF-12: "one series per selected
   unit"); the series unit shown in the verdict is the chosen unit if the table
   has it, else the table's most frequent one.

## Reaction round 1 (2026-07-13) — Variant B wins, built out

Maintainer: **B is the direction** ("very comprehensive overview"); C has other
use cases (kept, not built out); variant 0 gets re-homed near the data view
(wayfinder WF-22). Implemented in this round:

- **Full width** — the Registry tab drops the `lg2` container
  (`comparisonBoardMain.tsx`), the rail grows to viewport height.
- **Comparability-aware selection window** — every rail row carries a
  contract-computed dot for the chosen measure: ● merges · ● aggregate first · ●
  would block (tooltip names the WF-12 reason) · ● no data. Same pure function
  as the verdict, evaluated against the current selection; legend at the rail
  bottom.
- **Measure-first flow** — the measure select is now catalog-wide ("start
  here"), each option says how many sources provide it; picking a measure lights
  up the rail dots. The group-by select flags dimensions not present in every
  selected source ("some sources only" + warning helper) instead of silently
  dropping sources.
- **Stale-chart UX** — the hook tracks the parameters each run used; any change
  dims the chart under a "Parameters changed — Update chart" overlay (one click
  re-runs; auto-run was considered but hourly-scale queries make eager refetch
  jumpy — revisit if the overlay still feels clunky).
- Scenario-first selection noted as a seam in the rail header (needs the WF-14
  bundle-link harvest).

Still open for the next round: comparability beyond unit + substance
(agent-based-modelling context — map fog, feeds WF-14), preset prominence
(WF-18: possibly preset-only entry), eu_leg substance fix (WF-21, decided:
species-conditional `co2_emission`).

## Reaction round 2 (2026-07-13) — measure bar

- **Measure bar on top of the graph filters** — the measure select moved out of
  the toolbar into its own bar above them (it is the initially required
  selection), with per-scenario provider info ("Provided by 3 sources: AMIRIS
  Germany 2019 (2) · Ariadne (1) — 1 of 2 selected provide it") and a **"Select
  all N providers"** button (`ms.selectProviders`).
- **Ontology-hierarchy measure grouping** (maintainer idea, charted as wayfinder
  WF-23, not built): OEO verifiably groups per-species emission rates under
  `OEO_00140082` _greenhouse gas emission rate_ — subclass traversal could let
  sources annotating different subclasses meet at a parent class. Discovery
  grouping is the safe near-term use; a verdict leg needs double-counting and
  CO2e-weighting guardrails first.

## Reaction round 3 (2026-07-13) — no-data feedback + raw-data transparency

- **No blank graphs** — an empty result now renders a "No data for this query"
  panel naming the exact slice (measure, unit, granularity, number of sources)
  and suggesting what to change; all three variants.
- **Table peek** — every rail row carries a preview icon: a dialog with the
  first 8 raw rows of the table plus an "Open table page" link
  (`/dataedit/view/model_draft/<table>`), without leaving the composition.
- eu_leg awareness confirmed on the ticket: it blocks against everything because
  its species live in the `greenhouse_gas` DIMENSION while the measure concept
  is never emitted — WF-21 (decided) fixes the CO2 slice, WF-23 generalizes.

## Reaction round 4 (2026-07-13) — legend term resolution + zoom

- **No raw OEO ids in the legend** — IRI-valued group values resolve through the
  TIB Terminology Service (`../tibTerms.js`, same cache as the single-table
  view): TIB label first, registry enum label second, shortened IRI last. Legend
  entries show the ontology definition on hover, and a term-chip row under the
  chart links each series to its ontology term.
- **Zoom / range selection** — echarts `dataZoom` (wheel/drag inside the plot,
  range slider, toolbox zoom/restore) activates whenever the x-axis has more
  than 31 buckets — hourly and daily series over long periods are now navigable.

## Reaction round 5 (2026-07-13) — feedback pause; entry point charted

"Prototype looks good for now" — no build changes. The remaining issue is bigger
than this prototype: the comparison board is only reachable via scenario-bundles
listing → badge-select ≥2 scenarios → "Compare scenarios", although the Registry
tab never uses the selected scenario uids (only the Qualitative view does).
Charted as wayfinder WF-24 (entry-point rework, affects qualitative comparison
too); "okay for now" per the maintainer, so this prototype stays reachable
through the existing flow.

## Reaction round 6 (2026-07-13) — title, computation statement, measure picker, How it works

- **Generated chart title** — the chart writes out what is plotted ("Electricity
  price in EUR/MWh per month, grouped by source" + source list), built from a
  run-time snapshot (`ranSummary`) so it stays truthful while the stale overlay
  is up. The single-table view's title misses the measure — noted on WF-22.
- **Computation statement** — under the title, every run states what was done to
  the stored values: "✓ Plotted as stored — no aggregation and no unit
  conversion" for a pure merge, else per-source aggregation lines (function +
  registry-hint provenance) and, once WF-13 units exist, conversion lines. The
  live aggregation notices moved into this snapshot; the FAME bookings caveat
  stays a chart footnote.
- **Measure picker rework (Variant B)** — searchable Autocomplete, 460px wide,
  sort toggle (most sources first ↔ A–Z), and single-source measures summarized
  away by default with an explanatory caption + "show and search them anyway"
  toggle; group headers split "Comparable across sources" from "Single source
  only".
- **"How it works?" content** — the dead button on the comparison board toolbar
  now opens a per-tab dialog (`HowItWorks.jsx`); the Registry walkthrough
  explains rail dots, measure spaces, the verdict contract, the ladder +
  registry-hinted aggregation and the chart rules in user language.
- **Multi-measure charts** (not built) — charted as wayfinder WF-25: co-display
  of two+ measures (dual axes), pairing suggested semantically (part–whole,
  price×volume); cross-measure arithmetic stays out of scope.

## Reaction round 7 (2026-07-13) — picker controls into the dropdown, toolbar alignment

- **Measure picker controls moved inside the dropdown** — sort (most sources ↔
  A–Z) and the single-source show/hide live in a header of the Autocomplete
  popup, right where the user searches (custom `PaperComponent`;
  `onMouseDown preventDefault` keeps the input focused so using them doesn't
  close the popup). Nothing measure-related sits outside the field anymore.
  _Follow-up (same day):_ the controls are now **small circular icon buttons
  with hover help**, the usual filter idiom — sort-by-sources, sort-A–Z, and an
  eye toggle for the hidden single-source measures (badge shows how many are
  hidden; the tooltip explains why they are).
- **No more helper text under toolbar fields** — the "stacking is off while
  grouped by source" caption elevated the Chart style field and broke the row
  baseline. Replaced by an in-field lock indicator (visible whenever grouping by
  source blocks stacking; tooltip explains why and how to unblock) plus a "—
  locked by group-by" annotation on the disabled menu item. The Grouped-by
  field's "not in every selected source" helper got the same treatment (warning
  icon in the field, tooltip with the consequence).

## Reaction round 8 (2026-07-13) — facet semantics, enum-isolation hole, tooltip order

- **Enum-isolation hole closed** — the `qualifier` registry dimension's only
  enum value has `iri: null`; the isolation filter (built from enum IRIs)
  silently vanished, so (a) qualifier was OFFERED as a group-by for every table
  with any is-about triple and (b) grouping by it bound EVERY annotation —
  award, bid, and the substance _electrical energy_ itself (the irritating
  three-series plot, where "electrical energy" ≈ award + bid double-counted).
  Fix: a shared-predicate dimension without enum IRIs is un-isolatable →
  `askDimension` never offers it, `buildMergedQuery` refuses to group by it.
- **Facet-conflation guard** (the deeper WF-04 point: the MEANING is the
  combination of annotations) — verified live that biogas "electrical energy" =
  8,761 bid + 8,761 award observations: grouped by source they were summed into
  one series. Now the hook discovers which facet values the chosen measure
  spreads over in the selected sources (`facetValuesForMeasure`, one
  enum-isolated query); if a facet has ≥2 values and isn't the group-by, Variant
  B shows a warning ("bid · award are summed into one series") with a one-click
  "Group by Transaction Role" fix, and the chart carries a footnote (all
  variants).
- **Extraction verified faithful** — the "empty" investment-cost chart was
  correct data: AMIRIS Germany2019 reports investment/fixed/variable cost as
  all-zero (8,761 hourly rows × 0 per agent; market revenue €1.5e9 and energy
  8.09e7 MWh check out). The chart now says so: an info note "every value in
  this slice is exactly 0 — read correctly, nothing non-zero to see", and a
  separate guard replaces the empty coordinate system when rows carry NO
  readable numbers at all.
- **Tooltip ordering** — the hover listing sorts by value, largest first
  (`tooltip.order: "valueDesc"`), matching the visual order of the lines.
- A stale-HMR `ToggleButtonGroup is not defined` error was reported once (module
  timestamp predated the round-7 rework); no reference remains — hard reload
  clears it.

## Verdict

**Variant B (workbench rail).** Remaining before this directory dies: further
reaction rounds on the B build-out, then fold B into the real Registry view
(rewrite, not promote), delete A/C/the switcher/the `comparisonBoardMain.tsx`
mount — and keep `../comparability.js`.
