<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2026 Hendrik Huyskens <https://github.com/henhuy> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

- A tag looks the same everywhere: the house component `tag`
  (`base/templates/components/tag.html`), a pill in the tag's own colour with
  its text colour from `readable_text_color`, as a static label, a link that
  filters by the tag, a removable pill (the factsheet editor's current tags, now
  with a close button) or a toggle in a pick list. It replaces the tag
  renderings on the factsheet detail page (whose tags now link to the list
  filtered by them, instead of an empty `href`), the factsheet list (its filter
  and its tags column), the factsheet editor, the table list (no longer a dot in
  a grey badge), the table page and the tag overview. Statuses are the separate
  `badge` (`badge--success`, `--info`, `--warning`, `--danger`, `--neutral`): a
  light status colour and a small radius, never a pill. "Early Access" is an
  info badge instead of a red pill that read like an error, and the table list's
  "Reviewed" is a success badge. `.early-access`, `.success-badge`, the unused
  `tagged_field.html` and `oep-tags.js` (which only ticked the old tag
  checkboxes; the tick is CSS now) are gone. Both components have a catalogue
  entry [(#2683)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2683)
- A component catalogue at `/styleguide/` (public, not indexed, linked from no
  menu) shows every house component rendered from its entry template and as
  copyable source from the same file, under a table of every design token with
  its live value. `?tokens=bootstrap` renders it with Bootstrap 5.2's stock
  token values. The "Catalogue check" workflow now also runs
  `manage.py check_catalogue` (every component partial and include has an entry,
  and the page renders in both modes) and a literal scan in headless Chrome that
  fails when a component still paints an OEP colour under stock tokens. The
  theme's twelve component partials moved to `theming/scss/legacy/` (and
  `layouts/` for the collapse and sidebar rules), compiled unchanged. The first
  house component is `link_with_arrow`, the homepage's sliding-arrow link, now
  in the theme; the homepage renders pixel for pixel as before, and its arrows
  no longer slide for visitors who ask for reduced motion
  [(#2682)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2682)
- The theme now emits the platform's design tokens as CSS custom properties at
  `:root`: Bootstrap's `--bs-*` names where Bootstrap has one, plus a small
  `--oep-*` set (text, borders, surfaces, shadows, dense size, heading weight,
  reading width, content width, transition), with the homepage's values as
  defaults in `theming/_variables.scss`. A re-map layer points Bootstrap's
  component variables (buttons, fields and their focus ring, checkboxes,
  dropdowns, pagination, tabs, cards, dialogs, links) at the tokens, so one
  stylesheet that sets `--bs-primary` and `--bs-primary-rgb` recolours all of
  them, not just the navbar. The homepage and the navbar read only tokens and
  render pixel for pixel as before; `--primaryColor*` and `--white` are gone.
  Off the homepage two defaults change what renders: corners follow the radius
  scale (4px; 2px small; 8px on what floats, so buttons and pagination lose half
  their rounding), and `--bs-border-color` is the homepage's lighter `#e9f0f5`,
  which lightens table borders, `.border` utilities and dialog dividers.
  `benchmarks/homepage/compare.mjs` compares full-page homepage screenshots
  before and after a change
  [(#2679)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2679)
- The Bootstrap theme builds with one npm command, `npm run build:theme` (`sass`
  1.77.0 and `bootstrap` 5.2.0 as exactly pinned dev dependencies), instead of
  by hand in a Docker container, which is removed. The compiled
  `bootstrap.min.css` stays committed and is byte-identical. A new "Catalogue
  check" workflow rebuilds it on pull requests touching templates, CSS or the
  theme and fails when the committed file differs. `$success`, `$info`,
  `$warning`, `$danger`, `$light`, `$dark` and `$theme-colors` now reach
  Bootstrap, and `$border-radius-lg` is forwarded as itself (and set to the
  0.5rem that always rendered), so changing them in `theming/_variables.scss`
  takes effect
  [(#2671)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2671)
- The podman stack's Apache access log now records each request's user agent and
  the time it took to serve (`%D`, microseconds), appended to the end of the
  Common Log Format line so existing parsers keep working. Referer, cookies and
  the `Authorization` header are deliberately not logged. The maintenance guide
  documents the fields and a one-liner ranking paths by total server time
  [(#2670)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2670)
- The profile's datasets tab is one dense list of your own Datasets, replacing
  the cards: Dataset (title linked to its page, the name beneath), Status
  (Draft, or Published since a date), Tables (a count whose popover names the
  draft and embargoed members and the first ten by title), Topics, Modified and
  Created. An empty Tables or Topics cell on a draft reads "– needed to
  publish". It filters by search, status (with counts), Topic, Tag (a Dataset
  carries a tag when one of its members does) and, under "More filters", the
  Created and Modified dates; it sorts by every column but Topics, newest change
  first by default, 25 per page, with the state in the address. The columns
  collapse by the list's own width, measured in a browser (880 / 780 px, the
  rows stack below 630 px). The card routes are gone, and with them creating,
  editing, deleting and managing a Dataset from the dashboard until the row
  actions land; the API still does all of it. A multi-valued filter in a list's
  primary row is now a dropdown of checkboxes
  [(#2662)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2662)
- The profile dashboard's tables tab now runs on a generic list module, with no
  change in what it does: `login/static/login/dash_list.js` holds the behaviour
  (filter bar, selection, bulk bar, dialog, drawer, toasts) driven by a config
  of ids and event names, and `tables_tab.js` binds it to the tables tab. The
  styles split the same way into `dash_list.css` and `tables_tab.css`, and the
  column collapse is scoped to the tables tab, so another list's columns cannot
  collapse at its widths. `benchmarks/tables_tab/widths.mjs` takes the tab, its
  column sets, its id prefix and the filter-bar query as parameters
  [(#2630)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2630)
- Updated the homepage with new content and styling
  [(#2352)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2352)
- Datasets now have a lifecycle: a Dataset is a draft until it is published, and
  a new one starts as a draft. A draft is visible only to its creator: it is
  left out of the public topic list (for the creator too), its page, metadata
  JSON and API address answer 404 for everyone else exactly as an unknown name
  does, the table page's Datasets sidebar, the API list and the tables tab show
  only published Datasets plus your own drafts (marked as drafts), and a
  scenario bundle's link to it reads `resolvable: null`. Platform admins have no
  exception. Writes through the API reveal no more than a read: someone else's
  draft answers 404, someone else's published Dataset 403; the dashboard's
  dataset routes answer 404 for a Dataset that is not yours. Every existing
  Dataset is migrated as published since its creation (Django migration
  `dataedit.0058_dataset_lifecycle`)
  [(#2618)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2618)
- Dataset API: deleting a Dataset (`DELETE /api/v0/datasets/<name>/`) and
  changing its members (`assign-tables/`, `unassign-tables/`) now go through one
  Dataset action service, the path the dashboard will take too. A delete answers
  a bare 204 (the body is gone), and a repeat 404; the member Tables are never
  deleted. Each delete and each Table added or removed is logged on
  `oeplatform.dataset_actions`. The member routes take at most 2,500 Tables per
  call (more is a 400 naming the limit), and answer an unknown Dataset or
  someone else's draft with the same `{"detail": …}` 404 as every read. A
  Dataset's `modified_at` is now kept: set at creation, and moved whenever its
  membership really changes, from the API, the tables tab's "Add to dataset" /
  "Remove from dataset", or a member Table being deleted
  [(#2619)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2619)
- Dataset API: a Dataset can now go from nothing to published through the API
  alone. `POST /api/v0/datasets/` takes optional `topics` and answers with the
  new Dataset's read body; `PATCH /api/v0/datasets/<name>/` replaces `PUT`
  (which now answers 405): a key left out is left as it is, `topics` replaces
  the set, an omitted `at_id` keeps the stored one, and `name` is refused even
  when unchanged. An unknown topic or the draft pseudo-topic is a 400 naming it,
  never silently dropped. New `POST …/publish/` and `…/unpublish/` take no body
  and answer with the Dataset: publishing needs at least one member Table and
  one topic (the Dataset's Publish gate), and a Dataset that fails it is a 409
  listing the failed checks in `failed` (`members`, `topics`); republishing
  moves `published_at`, unpublishing a draft writes nothing. Every read carries
  `published_at`, `creator`, `topics` and `modified_at`; an update that changes
  nothing leaves `modified_at` alone, and publishing never moves it. Every
  Dataset refusal is DRF's `{"detail": …}` or field map, and each operation's
  success and refusal bodies are declared in the API reference. The resources
  read no longer claims a `schema` key it never sent
  [(#2620)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2620)
- Dataset API: `GET /api/v0/datasets/` and `GET …/<name>/resources/` are now
  paged, in DRF's `{count, next, previous, results}` envelope, by name, with
  `page` and `page_size` (20 if left out, at most 100); a page past the last is
  a 404. Clients reading either as a bare array must read `results`. The list
  takes `?mine=true` (the caller's own Datasets, drafts included; a 401 without
  a login) and `?published=true|false`, so `mine=true&published=false` lists
  your drafts; any other value is a 400 naming the parameter. List items are
  summaries: the Dataset's read body without `metadata.resources`, plus
  `resource_count`; the resources stay on the Dataset's own read and its
  `resources/`. Both lists cost the same few queries per page however many
  Datasets or members there are
  [(#2621)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2621)
- Profile dashboard, datasets tab: every row has a ⋯ menu with Publish… (or
  Unpublish… for a published Dataset) and Delete…. Publish says where the
  Dataset will be listed and how many of its tables are drafts or under embargo,
  which never stops it; a draft without tables or topics is told what it needs
  and cannot be confirmed. Unpublish and delete state their consequences;
  deleting a published Dataset asks for its name, and member tables are never
  deleted. The list refreshes in place, a message names what was done, and
  deleting the last Dataset shows the empty state without a reload. The
  dashboard never republishes; the API still does
  [(#2623)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2623)
- Profile dashboard, datasets tab: Create and Edit share one dialog with title,
  description and topics. "New dataset" ends the filter row and "Create a
  dataset" fills the empty state; Edit… is the first entry of each row's ⋯ menu
  and sits in the publish dialog beside a missing topic. While the title is
  typed, the dialog shows the web address it gives, or says that the name is
  taken or that the title needs a letter or number, and Create stays disabled
  until the name is free. A new Dataset is a private draft; a refused save keeps
  what was typed and names an unknown topic; a save that changes nothing changes
  nothing. The first Create in an empty account brings the filter bar in without
  a reload
  [(#2624)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2624)
- Profile dashboard, datasets tab: a members drawer, opened by "Manage tables…"
  in a row's ⋯ menu, by "and n more" in the Tables popover and by the publish
  dialog of a Dataset without tables. It lists every member, 25 per page with a
  search, and adds any table you may assign: your own before you type, anyone's
  published table once you search. Add and Remove act at once and the list
  refreshes behind the drawer; removing a draft or embargoed table you could not
  add back asks first. An add names the topics it brought along, and a link
  hands over to the tables tab for your own members. The open drawer is in the
  address (`?members=<name>`), so browser Back from that hand-off reopens it
  [(#2625)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2625)
- The term search in the metadata editor and the oeo_ext unit picker no longer
  always asks openenergyplatform.org: an instance with its own lookup service
  searches itself, one without uses the public endpoint, and `OEO_SEARCH_URL`
  overrides both (`EXTERNAL_URLS["oeo_search"]`). Search terms are now
  URL-encoded
  [(#2607)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2607)
- Speed up the row upload API: index the unapplied rows of the edit-journal meta
  tables (`_<table>_insert/_edit/_delete`, back-filled by an oedb migration),
  mark applied rows with one set-based update instead of a per-row OR chain,
  scan only the meta table relevant to the operation, and apply changes exactly
  once per request instead of twice. Also fixes applying a journal that held
  pending changes of more than one kind: the first change of each new kind was
  dropped and the apply then failed. The oedb migration builds the index for
  existing meta tables one at a time, so it neither write-locks all journals at
  once nor overflows Postgres' lock table on a large platform.
  [(#2362)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2362)
- For API clients: `tables/<table>/move_publish/<topic>/`, `unpublish/` and
  deleting a table now take the same path as the tables tab, with the same
  request and response bodies (`{}`, or `{"reason": …}` on a refusal) and one
  log line per call (`via=api`). Publishing writes everything or nothing: an
  unknown topic used to set the embargo before failing with "Invalid request",
  and now answers 400 naming the topic with nothing changed. Two requests that
  used to succeed now answer 400 with the reason: publishing under `draft` (a
  status, not a topic), and an embargo duration other than `none`, `6_months` or
  `1_year` (it used to be ignored). A missing open data license is still a 400,
  worded as the tables tab words it ("Fails the Publish gate: License").
  Unchanged: a published table can be published again under another topic, an
  omitted embargo leaves the existing one as it is, unpublishing a draft
  succeeds, and a published table can be deleted. If a table's record is deleted
  but its database table cannot be dropped, the delete answers 500 naming the
  table instead of 400 "Invalid request"
  [(#2569)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2569)
- The Django database port can be set with `OEP_DJANGO_PORT` in the
  `securitysettings.py` template, like the OEDB's `LOCAL_DB_PORT`. Without it a
  local database container could not be published on any port but 5432
  [(#2581)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2581)
- The dev image caches pip downloads and built wheels in a BuildKit cache mount
  instead of discarding them. A single new line in `requirements.txt` used to
  re-download and re-compile all ~47 packages, several minutes of it building
  `psycopg2`, `shapely` and `owlready2` from source. The image stays the same
  size, because the cache lives outside it
  [(#2436)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2436)
- Refactor user groups into organizations; add fields to the organization model;
  refactor HTMX for organization management pages
  [(#2261)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2261)
- Changing an account's email address at `/accounts/email/` now asks for the
  password again, as a password change already does. The previous address gets a
  mail when the address changes, and an account keeps one address: a new one
  replaces it once it is confirmed
  [(#2609)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2609)
- The account pages under `/accounts/` (email address, password prompt,
  connected accounts, inactive account, cancelled sign-in) use the OEP layout,
  and the settings page links them. An account that signs in through RegApp can
  set a password there and then disconnect RegApp. The unused second password
  reset under `/user/password_reset/` is removed
  [(#2610)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2610)

## Features

- A Table's Holders can be managed through the REST API:
  `GET`/`POST /api/v0/tables/<name>/permissions/` lists them and adds one, and
  `PATCH`/`DELETE .../permissions/user:<id>/` (or `org:<id>/`) changes or
  removes one. Every write goes through the same permission service as the
  access drawer, so every rule holds there too, and logs `via=api`. A change
  that takes your own Admin away answers `409` until it is sent again with
  `confirm`
  [(#2570)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2570)

- The tables tab of the profile dashboard shows one list instead of the draft
  and published card sections: every Table you can write, directly or through an
  organization, with its status and where your access comes from. A status
  segment with counts, a search, sorting, 25 rows per page and the whole state
  in the address bar. Publishing, unpublishing and deleting moved into each
  row's ⋯ menu (#2561, #2562)
  [(#2572)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2572)
- Each row of the tables tab now says whether the Table would pass the publish
  check (with the reasons and links to fix it on click, published Tables
  included), its review state with the badge linked to the review, how many
  datasets it is in (yours first, never another user's draft) and its topics.
  The list sorts by review state and by dataset count too
  [(#2554)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2554)
- The tables tab filters by review state, by where your access comes from
  (direct or one of your organizations), by dataset (in any, in none, or one),
  and behind "More filters" by topic (any of) and tags (all of). Options come
  from your own tables only. Active filters show as removable chips with "Reset
  all", and a value from an old link that no longer applies shows as a muted
  chip instead of emptying the list
  [(#2556)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2556)
- The tables tab fits its width without sideways scrolling, from a wide screen
  to a phone: as the list narrows, Topics drops first, then Review and Datasets,
  and on the narrowest screens each row stacks into two lines with a "Sort by"
  select in place of the column headers. Where the filter bar does not fit on
  one line, everything but the search folds behind "Filters (n)". Long
  organization names are shortened in the Access column, in full on hover
  [(#2555)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2555)
- Whether a Table passes the publish check is now stored with it and recomputed
  on every metadata write, so the tables tab filters by "Publishable" and sorts
  by it (not publishable first). Publishing itself still checks the metadata at
  that moment. Deploy: run `python manage.py migrate`, then
  `python manage.py recompute_publish_gate --apply` once; until it has run, the
  Publishable filter matches no existing Table
  [(#2560)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2560)
- Every row of the tables tab has a ⋯ menu: edit metadata, upload data, and
  publish (topic and embargo in a dialog) or unpublish, without a page reload or
  an alert. An action above your role on that table stays in the menu, disabled,
  with the reason. The dialog says first what would be left out and why; the
  server checks again and changes nothing if anything changed in between. The
  list then refreshes itself, keeping its filters, and a message says what
  happened. Each action writes one log line per table
  [(#2561)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2561)
- A Table now records when its content last changed, its data (rows, a bulk
  upload, columns and constraints) and its metadata separately. Publishing,
  unpublishing, embargoes and role changes do not count. The tables tab shows
  the later of the two in a new Modified column, sorts by it by default (newest
  first, tables with no recorded change last) and filters by a Modified date
  range under "More filters". Nothing was recorded before this release, so
  existing tables show "–" until they next change. Deploy: run
  `python manage.py migrate` (`dataedit.0056`, two empty columns)
  [(#2557)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2557)
- A Table now records when it was created, and the tables tab shows it in a new
  Created column, sortable (unknowns count as the oldest) and filterable by a
  Created date range under "More filters". Tables created before November 2025
  read "before Nov 2025": the field they used to be dated by (`date_updated`)
  holds a date their metadata declared, not when they were created, and no
  record of that exists. Such a table matches a Created range only with no start
  and an end on or after 30 Oct 2025, the only ranges that certainly hold it.
  `date_updated` itself is unchanged. Deploy: run `python manage.py migrate`
  (`dataedit.0057`, one column, filled from `date_updated` for tables above id
  69915 only, measured on production)
  [(#2559)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2559)
- Existing tables get the data half of their Modified date where one can be
  recovered: the latest applied change in their edit journal or their latest
  successful bulk upload, whichever is later. The new command
  `python manage.py backfill_data_modified` is a dry run that counts what it
  found; with `--apply` it fills only tables that have no date yet, so a date
  stamped since the release is never overwritten and a second run changes
  nothing. It only reads the OEDB, and never creates a missing journal. The
  metadata half stays empty, because no metadata save was ever timestamped.
  Deploy: run it once after `dataedit.0056`
  [(#2589)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2589)
- The tables tab's ⋯ menu adds a table to one of your own datasets, or removes
  it from one (offered only when one of yours holds it). A draft or embargoed
  table may be added by anyone holding Data editor on it, directly or through an
  organization: before, a draft you could write only through an organization was
  offered on the Datasets tab and then refused. The dataset assign API and the
  Datasets tab follow the same rule, and the API's assign and unassign now
  change all the named tables or none
  [(#2563)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2563)
- Tables can be deleted from the ⋯ menu of the tables tab again, published ones
  included (Data maintainer or above). A draft asks for a plain confirmation.
  For a published table the dialog says what deleting breaks (the datasets it
  leaves, other people's named with their owner, its review state, an active
  embargo, and that links from scenario bundles stop resolving) and asks you to
  type the table's name. A batch holding a published table or more than ten is
  confirmed by typing the number of tables, and at most 50 are deleted at once.
  If the database table cannot be removed after the table's record is gone, a
  warning that stays on screen names it, and the log says `drop=failed`
  [(#2562)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2562)
- A table's Access cell, or "Manage access" in its ⋯ menu, opens a side drawer
  listing who holds which role (Data editor, Data maintainer, Admin), your own
  entries marked. A Table admin adds a person or one of their own organizations
  with a role in one step, changes or removes any holder; everyone else sees the
  list read-only with the table's Admins, and anyone with a role of their own
  can leave the table. Organizations go up to Data maintainer, Admin is given to
  people by name, and a table always keeps one person with Admin. Losing your
  own Admin, or the table from your dashboard, asks once. The drawer stays open
  while the list refreshes behind it; each change writes one log line with the
  role before and after
  [(#2566)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2566)
- Tables in the tables tab can be selected and published or unpublished in one
  go. Each row has a checkbox, the header ticks the page, Shift+click ticks a
  range, and "Select all N matching tables" takes every table under the current
  filters across all pages. The selection survives paging, sorting and actions,
  and is cleared, with a note, when the filters or the search change. A bar
  above the list shows how many are selected; its place is kept while nothing
  is, so the list does not move on the first tick. Publish takes one topic and
  embargo for the whole batch and leaves out, by name and with the reason,
  tables already published, tables failing the publish check and tables you are
  not Table admin of. Unpublish names other people's datasets that will then
  hold a draft. At most 1,000 tables are published or unpublished at once, and a
  batch is done whole or not at all
  [(#2564)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2564)
- The selection bar of the tables tab can also delete the selected tables and
  add them to, or remove them from, one of your own datasets. Bulk delete lists
  every table, marks the published ones and counts what deleting breaks: how
  many are published, reviewed or under embargo, which datasets lose how many of
  them (other people's with their owner), and the links from scenario bundles
  that stop resolving. A batch holding a published table or more than ten is
  confirmed by typing the number of tables, at most 50 at once, and every table
  whose database table could not be removed is named in a warning that stays on
  screen. Choosing the dataset re-checks the selection on the spot and names the
  tables already in it (add) or not in it (remove); at most 2,500 tables are
  added or removed at once, all or none
  [(#2565)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2565)
- Tables tab: the bulk bar can share the selected tables with one of your
  organizations as Data editor or Data maintainer, or remove an organization
  from them. A share only ever raises a role: tables where the organization
  holds that role or more already stay unchanged and are named. A removal leaves
  out the tables where the organization's old Admin grant is the only Admin
  ("give someone Admin there first") and names the tables you would lose access
  to before you confirm. Both dialogs state the organization's member count,
  re-check the selection as you choose, leave out tables you are not a Table
  admin on, and write all tables or none, at most 2,500 at once, with one log
  line per table changed
  [(#2568)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2568)
- Tables tab: a bulk dialog's title counts what its list counts, the tables the
  action acts on, and says out of how many were selected ("Delete 14 of 16
  tables", "Will be deleted (14)", "Left out (2)"). The dialogs name datasets by
  their title, and unpublish says how many of the tables each of other people's
  datasets holds. Where the rows stack on a narrow screen, "Select this page"
  selects and clears the visible page and offers "Select all N matching tables",
  as the header checkbox does on a wider one
  [(#2596)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2596)
- REST API: share many tables with one of your organizations, or remove an
  organization from many tables, in one request, under the same rules as the
  dashboard's bulk bar: all tables or none, a share only raises a role, a
  repeated removal succeeds, at most 2,500 tables at once
  (`POST /api/v0/organizations/<id>/table-permissions/share/` and `…/remove/`).
  And everywhere a table's access is managed (the access drawer, the table's
  permission page, the API), removing or lowering an organization's old Admin
  grant that is the table's only Admin is now refused instead of leaving the
  table with no Admin at all
  [(#2595)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2595)

## Bugs

- Six small defects found while rendering the platform for the design work: an
  unknown research project page answers 404 instead of a server error; an
  unknown factsheet type (`/factsheets/<anything>s/` and every page under it)
  answers 404 instead of an empty list or a server error; the profile's Reviews
  tab loads its script as a module, so the browser no longer refuses it; a stray
  `^` no longer shows above the navbar of the table view; the help tooltips on
  model and framework factsheets open again; and the framework factsheet's
  sections get the card padding the model factsheet has, with no table row
  nested in another
  [(#2634)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2634)
- Tables tab: a Table named `actions` can open its access drawer again. The
  dashboard's action, check and "select all" routes moved beside `tables/`
  (`profile/<id>/table-actions/…`, `…/table-names`), so no Table name collides
  with them; their URL names are unchanged
  [(#2611)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2611)
- The privacy policy names the platform's own domain, openenergyplatform.org,
  for the site and its cookies instead of openenergy-platform.org, which only
  redirects there. Three typos in the terms of use are corrected
  [(#2615)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2615)
- Errors on the sign-up, set-password and reset-password forms are shown as
  errors (red) instead of green "success" alerts, and the reset-password form
  shows its errors at all: it looked for them on a field it does not have.
  `securitysettings.py.default` no longer lists a login provider with an empty
  `provider_id`, which made the sign-in and sign-up pages fail on a fresh setup
  [(#2608)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2608)
- Saved table views (graph and map views, the default view) can only be created,
  changed or deleted by someone with write permission on the table; the "Add …
  view" links are shown only to them. Saving a view now finds it only within its
  own table
  [(#2601)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2601)
- Running the test suite no longer deletes your own tables. The tests used the
  data database configured for the platform, and one of them clears its whole
  sandbox schema, which took the dev container's example table with it while its
  record stayed behind (the metadata editor then showed it without columns). A
  test run now uses a data database of its own, `test_<name>` or
  `LOCAL_TEST_DB_NAME`, which the test runner creates and migrates. And
  `create_example_tables` now leaves a complete example table however often it
  runs: it repairs a record whose table is gone, seeds the schema the table is
  really in (it never had its 4 rows before), and no longer fails to create its
  fallback user
  [(#2602)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2602)

- Deleting a table removes its peer reviews with it. A review names its table
  only by name, so a table created later under the same name used to inherit the
  old review state and badge. Dropping a deleted table's database tables now
  gives up after waiting 1 s for another session's lock instead of waiting until
  the request times out; it is then reported as a table that could not be
  removed, as any failed drop is
  [(#2597)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2597)
- The metadata editor no longer hangs on a table whose column carries a very
  long annotation list. A column with 4,525 value references never finished
  loading, because the form library's cost grows with the square of a list's
  length. Lists over 200 entries are now kept out of the form with a notice
  saying so, and are saved and downloaded unchanged, together with any entries
  added in the form
  [(#2593)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2593)

- Finishing a peer review now writes the merged metadata the way every other
  metadata write does: it is validated, and the table's displayed title and its
  search entry follow the accepted values. Before, a review that accepted a new
  title left the old one on the table page and in lists, and the search kept
  finding the pre-review words. A merge that fails validation is refused with a
  readable message and writes nothing: the review stays unfinished, and no badge
  or "reviewed" flag is set
  [(#2552)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2552)
- The table page no longer stores a new saved view on every visit. Production
  had collected ~195,000 of them, scanned twice per page view. A migration
  removes the empty copies and adds a unique constraint on (table, type, name),
  which keeps them out and indexes the lookup; saved views that carry filters or
  options are never deleted, and if two of them share a name, one is renamed
  "name (id)". Saving a view under a name the table already uses now says so
  instead of failing, a graph marked as default no longer replaces the Table
  tab, and setting the default view or deleting a view requires POST
  [(#2218)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2218)
- The docker development setup works on macOS: bind-mounted folders are given to
  the container user by numeric id (macOS' group id already exists in the image,
  so the named group was never created), and a `.DS_Store` left by Finder no
  longer stops the OEO version lookup, the ontology module list or the about
  page. The build context now leaves out `.git/`, `static/`, `data/` and cache
  files at any depth, which also applies to the production images
  [(#2344)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2344)
- Deleting a peer review now checks the caller: only its reviewer or a platform
  admin may delete it
  [(#2544)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2544)
- Restrict profile pages to their owner and check organization permissions
  before saving
  [(#2547)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2547)
- A table's permission page follows the same rules as the dashboard's access
  drawer: adding a person or organization takes a role in the same step, "None"
  is no longer offered, organizations go up to Data maintainer and can be added
  only by their members, a table always keeps one person with Admin, and losing
  your own Admin asks once. A refused change is shown as a message on the page
  and writes nothing; before, an unknown user name was a server error, any
  number was stored as a level, and the last Admin could remove themself. Each
  change writes one log line (`via=table-page`). Error messages across the site
  are now shown in red
  [(#2567)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2567)
- Browsers no longer keep last release's stylesheets and scripts after a deploy.
  Static files are now named after their content (`css/base-style.<hash>.css`),
  so a changed file gets a new address. For deploys: run `collectstatic` before
  `compress`, and run `compress` under the same `DEBUG` as the server, or no
  page renders. The Podman image now builds with `OEP_DEBUG=False` for that
  step. `collectstatic` now refuses a stylesheet whose `url()` points at a
  missing file. The 18 such references in the vendored jQuery UI and Leaflet
  stylesheets are removed (they never loaded), and so is the unused
  `filterform.css`
  [(#2604)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2604)

## Documentation updates

- Reworked the pull request template: sections for testing, deploy notes and a
  new "For reviewers" block; the changelog line is now written only in the
  changelog; fixed the broken reviewer-guidelines link
  [(#2603)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2603)

## Code Quality

- Profile dashboard: the tables tab's views, page and results region are now
  generic bases (`login/list_views.py`, `list_tab.html`, `list_region.html`)
  that the coming datasets tab subclasses instead of copying, and the list
  mechanics (`login/listing.py`) have their own tests. Nothing visible changes
  [(#2616)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2616)
