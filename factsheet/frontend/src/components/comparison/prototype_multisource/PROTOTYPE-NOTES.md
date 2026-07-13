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

## Verdict

**Variant B (workbench rail).** Remaining before this directory dies: further
reaction rounds on the B build-out, then fold B into the real Registry view
(rewrite, not promote), delete A/C/the switcher/the `comparisonBoardMain.tsx`
mount — and keep `../comparability.js`.
