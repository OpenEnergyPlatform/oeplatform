<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

- The scenario-bundle changelog page under Factsheets now also lists changes
  made through the REST API. Those rows show who changed what and when, but no
  side-by-side diff: the API records what changed in a newer form that this page
  does not read yet
  [(#2441)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2441)

- The dev compose stack names the graph store host explicitly
  (`RDF_DATABASE_HOST: fuseki`) and waits for that service. Previously it relied
  on the local `securitysettings.py`, whose shipped default resolves the host to
  `localhost` -- which inside the container is the container itself, so the OEKG
  API answered `503` instead of writing
  [(#2435)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2435)

- Model/Framework factsheet overviews load in a fraction of the time. The row
  data is built by the server in one pass instead of being assembled in the page
  template (2,138 database queries down to 3, whatever the number of
  factsheets), the sidebar lists each tag actually in use by that sheet type
  once instead of one checkbox per tag assignment, and the page ships the eight
  columns the table shows rather than all 173. The rest of the columns are
  fetched once in the background on the first column toggle or search, so
  searching still matches hidden columns. Sorting, paging, the tag filter and
  the CSV download behave as before.
  [(#2346)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2346)

- The tag filter on those overviews is now kept in the page address
  (`?tags=<tag>,<tag>`), so a filtered view can be reloaded, bookmarked and
  shared, and the CSV download follows the same filter. Old links keep working.

- Clicking a tag shown on a row in the factsheet overviews now filters by that
  tag, and a "Clear tag filter" button switches the filter back off. The tags
  were rendered as links to nowhere, so a click reloaded the page and looked as
  though filtering had silently failed.

- The tags in the factsheet editor look like tags again. Each was written with
  two `class` attributes, and a browser keeps only the first, so the styling
  that gives them their shape was silently discarded and they rendered as bare
  coloured rectangles pressed against each other. Selecting one no longer
  resizes it and shifts its neighbours around either.
  [(#2346)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2346)

- Deleting a Model/Framework factsheet is possible for any logged-in account for
  one week after it was created, and for administrators at any time; the server
  refuses it rather than merely hiding the button, and every create, update and
  delete now leaves a log line. Editing stays open to everyone. Note that the
  window depends on the factsheet's age, not on who created it, and that a
  deletion cannot be undone - this part of the platform keeps no history.
  Existing factsheets stay administrator-only.

- The tag pages under Database are one screen: the create/edit form opens beside
  the list, a rejected name comes back with what you typed, and the form reports
  how many tables **and** factsheets carry a tag before you delete it - they are
  one shared vocabulary. The Database topic list and the factsheet overviews now
  link there; previously nothing on the platform did.

- Creating and editing a factsheet now happens under the same header band as the
  rest of the site, with a breadcrumb back to the overview and to the factsheet
  itself.

- Every list of tags on the platform can now be searched and sorted - the tag
  administration page, the Tags tab of the factsheet editor, and the tag filter
  on the factsheet overviews. All three showed the whole vocabulary at once,
  which at 800+ tags is unreadable. The filter on the overviews additionally
  starts with the ten tags most used by that sheet type and offers to show the
  rest; a tag you have already selected stays visible. "Most used" counts what
  actually carries the tag, and any tag stays reachable by typing part of its
  name. On the administration page the list sits in its own scrollable box with
  the actions above it, so a growing vocabulary no longer pushes "Create new
  Tag" off the screen. Sorting by name puts digits in numeric order, so "run 2"
  comes before "run 10". In the factsheet overviews' sidebar the column chooser
  now sits above the tag filter, so expanding the tags cannot push it out of
  view.

## Features

- The REST API now describes itself. `GET /api/v0/schema/` returns an OpenAPI
  description generated from the code itself, and `/api/v0/open-api/` renders it
  as a browsable Swagger page you can read the endpoints from. Because it is
  generated rather than written by hand, it cannot fall behind the API it
  describes: every endpoint appears the moment it is routed. The dataset
  endpoints additionally carry summaries, request examples and documented
  responses, and related endpoints are grouped so the page can be navigated
  [(#2398)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2398)

- The OEKG scenario-bundle REST API: `POST /api/v0/scenario-bundles/` creates a
  bundle and `GET /api/v0/scenario-bundles/<uid>/` reads it back. The server
  mints the identifier, the acronym is enforced unique on creation, the bundle
  is validated against the canonical SHACL shape **before** anything is written,
  and the write is one atomic request. Reads are public; writes need
  authentication
  [(#2435)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2435)

- `PATCH /api/v0/scenario-bundles/<uid>/` changes single fields of a scenario
  bundle without sending the rest. A field the payload does not name is left
  alone; a set-valued field it does name is replaced whole, and emptying one the
  shape requires is refused rather than silently applied. Only an owner may
  write - a bundle with no recorded owner stays administrator-only. Every bundle
  now carries a version, returned as an `ETag` on reads, and a write must send
  it back as `If-Match`: without it the request is refused (`428`), with a
  version that is no longer current it is refused (`412`), and if the bundle
  moves while the request is being prepared nothing is written and the answer is
  `409`. The version check is part of the write itself, so two clients cannot
  both succeed against the same version. Note that acronym uniqueness is
  enforced when a bundle is created but not when one is renamed, so a patch can
  still give two bundles the same acronym
  [(#2438)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2438)

- Creating a bundle now binds the acronym uniqueness check inside the write, so
  two simultaneous creates can no longer both take an acronym both of them found
  free [(#2438)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2438)

- Every write to a scenario bundle through the REST API now leaves a record, and
  `GET /api/v0/scenario-bundles/<uid>/history/` reads it back. Previously only
  the browser's edit path recorded anything, so creates and API writes were
  silent. An entry says which operation it was, who made it, when, which version
  it produced, and which triples changed; the reader renders those as field
  names and returns the raw triples on `?expand=triples`. The history is public
  but per bundle and paginated, and names the actor by username rather than by
  internal id. Entries written before this release are kept exactly as they are
  and read as coming from before the API
  [(#2441)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2441)

- Scenario factsheets are now addressable through the REST API: `POST`, `GET`
  and `PATCH` under `/api/v0/scenario-bundles/<uid>/scenarios/`. A bundle can
  also be created with its scenarios in a single call, which is what a modelling
  pipeline needs; a bundle `PATCH` still cannot reach into one, so no call can
  drop a scenario by leaving it out. Writes use the containing bundle's version
  and ownership, and a read of a scenario carries the bundle's `ETag`
  [(#2444)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2444)

- A read of a scenario bundle now includes its scenarios, so what you read is
  what a create accepts back
  [(#2444)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2444)

- Study reports - the publications a scenario bundle is written up in - are now
  addressable through the REST API: `POST`, `GET` and `PATCH` under
  `/api/v0/scenario-bundles/<uid>/study-reports/`, and accepted nested on a
  bundle create like scenarios are. An author may be shared between reports and
  between bundles, so a write may reference an existing one by its identifier
  but can never rename it - renaming would change every bundle citing that
  person. The link to the published document is stored as the document's own
  address rather than as text beside it
  [(#2452)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2452)

- A scenario's input and output datasets can now be linked through the REST API:
  `POST` and `GET` under
  `/api/v0/scenario-bundles/<uid>/scenarios/<sid>/datasets/`. A link says which
  direction it is and whether it points at one OEP table or at a whole OEP
  dataset - the first is the reproducible citation, the second stays current as
  the dataset's membership changes. There is deliberately no way to edit a link:
  everything it holds follows from those three answers, so it is added or
  removed. A link is never checked against what it points at and never stops
  anyone deleting it: a bundle is a published record, so "this scenario used
  that table" stays on the record afterwards, and nobody's citation can hold
  somebody else's data hostage. The same target cannot be linked twice in the
  same direction. This supersedes the older `manage-datasets/` route, which
  writes relations the canonical shape does not validate and no identifier at
  all [(#2452)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2452)

- A scenario factsheet, a study report or a dataset link can now be removed
  through the REST API: `DELETE` on its own URL, carrying the bundle's version
  as `If-Match` and nothing else - the retyped acronym guards a whole-bundle
  delete and nothing smaller. What goes with it is bounded by type: the part
  itself and, recursively, only the parts nested inside it, so a scenario's
  dataset links go with the scenario rather than being left behind unreachable.
  Everything else it pointed at - regions, authors, contacts, organisations,
  funders, cited documents, models, frameworks and every picked ontology term -
  is unlinked and never deleted, because other bundles cite those same nodes and
  removing one would make their records invalid. Before anything is removed the
  server checks whether something outside this bundle still points at it; if so
  the node is kept and only unlinked, and the response says which. Every delete
  is recorded in the bundle's history with the triples it removed
  [(#2456)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2456)

- A whole scenario bundle can now be deleted through the REST API, in two
  deliberate steps: read it, then `DELETE` its URL carrying both the version as
  `If-Match` and the bundle's acronym retyped as `?confirm=<acronym>`. The two
  guard different mistakes - the version catches a bundle somebody changed since
  you looked, the acronym catches the wrong bundle entirely, which is what a
  script looping over identifiers actually gets wrong. Deleting a bundle that is
  already gone answers "not found", which a client may treat as success after a
  lost response. What goes with it is bounded by type, as for a part: the
  bundle's own scenarios, study reports and dataset links, while regions,
  authors, contacts, organisations, funders, cited documents, models, frameworks
  and every picked ontology term are unlinked and never deleted - and anything
  another bundle still points at is kept, with the response saying which. The
  bundle's ownership records go with it, and the version bookkeeping the
  browser's own delete leaves behind is removed too. In the history the bundle
  keeps one line saying who deleted it, when, and under which acronym, while the
  contents of its earlier entries are pruned - so deleting really deletes, and
  the record that it happened survives
  [(#2470)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2470)

- Changing a scenario bundle through the REST API is now judged by what the
  change adds, not by whether the whole bundle is perfect. Bundles written
  before the API exists often miss fields the shape requires - a sector, a
  technology, an author - and those are exactly the fields somebody would add by
  editing. Previously the edit was refused for the very thing it came to fix, so
  none of the existing bundles could be changed at all. A write that adds a new
  problem is still refused, and the refusal now also says how many problems the
  bundle already had. Creating a bundle still has to be complete

- New management command `repair_oekg_shape_violations` fixes the
  scenario-bundle data that no longer matches the shape it is validated
  against - as far as a machine can. It reports by default and changes nothing
  without `--apply`, and writes a JSON record of every change before making it.
  Only the safe repair runs by default; the two that lose or invent information
  have to be asked for by name, and the command says which entry it dropped and
  which date it made up
  [(#2449)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2449)

- New management command `repair_factsheet_tags` repairs the factsheets the old
  tag editor damaged - on production 23 of 339 carry a copy of the whole tag
  table, holding 95% of all factsheet tag assignments. It reports by default and
  changes nothing without `--apply`, writes a JSON record of what it removed,
  flags borderline factsheets for a human decision, and dates each factsheet's
  damage so it is possible to say which backup would still recover its real
  tags. Repaired factsheets are set to zero tags; that loss is deliberate and
  recorded.
  [(#2385)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2385)

- A scenario bundle's change history now names the fields a write to one of its
  parts changed. Previously only a change to the bundle's own fields was named;
  a change to a scenario factsheet or a study report read back as a list of raw
  predicates, which is what the history exists not to be
  [(#2452)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2452)

## Bugs

- Error responses from the scenario-bundle API carried the text `"None"` where
  they should have carried an empty value, and would have turned numbers into
  text. Introduced in the previous release cycle and not shipped
  [(#2447)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2447)

- Pin `vite` to 8.0.13. From 8.0.14 the dependency pre-bundler emits chunks that
  reference an initialiser another chunk no longer defines, so any page using
  MUI with `@emotion/react` — the scenario-bundle UI among them — dies on
  `Uncaught ReferenceError: init_emotion_react_esm is not defined`. Upstream:
  vitejs/vite#22499, rooted in rolldown#9502

- The factsheet tag editor no longer attaches every tag on the platform. Opening
  a factsheet for editing pre-checked all ~825 tags, so saving attached the
  lot - one query per tag, which is what made saving take minutes. It now shows
  only that factsheet's tags, saves exactly what was selected, keeps the
  selection when validation fails, and no longer wipes tags on a submit that
  does not carry the tag widget. New: "remove all tags" and a live count.
  [(#2385)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2385)
  [(#2381)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2381)

- A CSV download with a tag filter applied returned a file containing only the
  header row, with no error - the page sent a value the download endpoint did
  not recognise, so it matched nothing.
  [(#2346)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2346)

- Tag administration: deleting a tag was possible for any logged-in account
  (while the button was shown to nobody, not even administrators); creating a
  tag whose name matched an existing one apart from capitalisation or
  punctuation silently renamed and recoloured that existing tag everywhere it
  was used; and a single tag with an unusual internal name made the whole tag
  overview fail to load.
- The OEKG REST API gets its own transport to the graph store
  (`oekg/graph_store.py`): one SPARQL request per write, which Fuseki treats as
  one transaction, instead of one committed request per triple. Its tests run
  against a real store in an isolated named graph, and skip with a stated reason
  when no store is reachable
  [(#2429)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2429)

- `python manage.py fetch_oekg_shapes` obtains the canonical OEKG SHACL shape
  from a pinned revision of the `oekg` repository, and generates the
  `rdfs:label` subset validation needs from the OEO release already on disk
  [(#2428)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2428)

- The generated OEO label subset copied labels verbatim, so 1,855 of 2,058
  carried an `@en` tag and four terms carried two labels. The shape requires
  `sh:datatype xsd:string` and `sh:maxCount 1` on `rdfs:label`, and a
  language-tagged literal is `rdf:langString` — so every picked OEO term failed
  validation. Labels are normalised to one plain string per term
  [(#2435)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2435)

- The OEKG SPARQL endpoint test patched `oekg.utils.execute_sparql_query` while
  the view binds that function into its own namespace, so the mock never took
  effect and the test made a real network call to a host that only resolves
  inside the compose network. It failed on every local run. Patched at the right
  name, it is now hermetic
  [(#2429)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2429)

## Documentation updates

- The scenario-bundle architecture guide now documents the **second** write
  path. The feature has had two since the REST API landed - the browser's, which
  writes triple by triple, and the API's, which validates the whole bundle
  against the canonical shape and then writes it in one atomic request - but
  only the first was described. The new section explains what differs before
  someone changes it (one request is one transaction, the shape is checked on
  the result rather than on the change, a write is refused only for problems it
  adds, and every write is guarded by the bundle's version) and generates the
  module reference from the source, so it cannot drift. The reference for the
  browser's views is no longer generated on two pages at once; the feature
  overview links to the guide that owns it
  [(#2458)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2458)

- The scenario-bundle developer documentation said the sector-division and
  study-descriptor dropdowns were hardcoded lists. Both have been served from
  the OEO for some time; the page now describes where each list actually comes
  from, that a division can be modelled either as individuals or as a class
  whose members point back at it, and which components read the descriptors and
  by which route
  [(#2450)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2450)

- Scenario Bundles and Model & Framework Factsheets list both of their pages in
  the navigation. The overview page was the section's own landing page and so
  had no entry of its own, which left each section looking as though it held a
  single sub-page
  [(#2450)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2450)

- New feature documentation for Model/Framework factsheets on mkdocs: what the
  pages do and who may do what, plus an architecture page recording how the list
  page is built, the release order for the tag repair, and the test seams.

## Code Quality

- Remove `StudyDescriptors.js`, the hardcoded study-descriptor array replaced by
  the OEO-served list. Nothing imported it any more
  [(#2450)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2450)
