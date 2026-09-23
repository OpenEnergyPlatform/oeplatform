<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

- The link to the tag manager on the Database pages is now a _Manage Tags_
  button in the Database introduction, beside Contribute Data, API Access and
  OEMetaBuilder. It was a sentence below the last topic card, far from the tag
  search it belongs with, and it appeared on the topic overview only

- The dev compose stack's vite container now reinstalls its dependencies when
  the lockfile moves. The marker recording which lockfile was installed sat at
  the repository root, which is a bind mount, while `node_modules` is a named
  volume -- so the marker could describe a dependency tree it had never seen,
  and the check stayed silent while the container ran a vite the lockfile no
  longer pins. A rebuild did not help either, because docker only seeds a named
  volume while it is empty. The marker now lives inside `node_modules`, and a
  reinstall drops the prebundled dependencies belonging to the old tree

- The _About -> REST-API Documentation_ link in the page header now opens the
  Web-API section of the developer documentation, which leads with the generated
  API Reference and lists the guides beside it. It pointed at one guide -
  "Working with the OEDB" - so the page describing every endpoint of the API was
  reachable only by noticing a link in that guide's second paragraph. The link's
  setting is also no longer called `readthedocs`; that documentation was retired
  and redirected here some time ago
  [(#2507)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2507)

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

- Scenario bundle addresses now open something. Every bundle is named by an IRI
  under `https://openenergyplatform.org/ontology/oekg/`, and those addresses are
  in published citations and in the graph's own triples -- but following one
  used to land on an ontology term page for a term that does not exist. A bundle
  address, and a scenario address, now redirect to the bundle's page in the
  browser, or to its representation in the REST API for a client asking for RDF.
  The addresses themselves are unchanged
  [(#2501)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2501)

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
  both succeed against the same version
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

- Scenario bundles can now be listed and searched through the REST API:
  `GET /api/v0/scenario-bundles/`. An entry says what it takes to choose a
  bundle - its acronym, its label, its identifier, its version and how many
  scenarios and study reports it holds - and not the bundles themselves, so the
  listing stays the same size as the corpus grows. `?acronym=` finds one bundle
  by the name it is known under, which is how a script that keeps nothing
  between runs finds the bundle it wrote last time, and the answer carries the
  version its next write has to send. The filters the scenario-bundle search
  offers carry over - organisation, funder, author, study descriptor, scenario
  year and publication year - named the way the API names those fields
  elsewhere, and either end of a year range now works on its own. The listing is
  paginated and there is no way to ask for all of it at once
  [(#2472)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2472)

- A read of a scenario bundle, a scenario, a study report or a dataset link can
  ask for the ontology terms it picks to be resolved to their names:
  `?expand=labels`. The names come from the small label subset the platform
  already keeps beside the shape, never from the full ontology, and they arrive
  beside the payload rather than in it, so what you read can still be sent
  straight back. A term with no name in the subset is reported as such rather
  than left out. An `expand` value no endpoint offers is refused rather than
  ignored, so a misspelling is not silently answered with an unresolved
  representation
  [(#2472)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2472)

- A scenario bundle can now be fetched as RDF: `Accept: text/turtle` or
  `application/ld+json` on its own URL returns the bundle's subgraph as the
  graph store holds it, carrying the same version tag the JSON read does. Writes
  stay JSON - that is where the payload is validated - so a write that asks for
  RDF back is refused rather than answered in a form it could not have been sent
  in [(#2472)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2472)

- Renaming a scenario bundle onto an acronym another bundle already holds is now
  refused. Uniqueness was enforced when a bundle was created and not afterwards,
  which left a rename able to make a lookup by acronym ambiguous - and a lookup
  by acronym is how a pipeline finds its own bundle. The check is part of the
  write itself, so two simultaneous renames cannot both take the same acronym,
  and a bundle never counts against itself, so sending back the acronym you just
  read is not refused by its own value
  [(#2472)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2472)

- A scenario's dataset links now say whether what they cite is still there.
  Every read of a link reports whether the named OEP table or dataset still
  exists, which tables the citation resolves to today, and whether each of those
  has been through Open Peer Review - finished, in progress, or no review at
  all, told apart rather than collapsed into a boolean, because most of the
  platform's data predates the review process and "not reviewed" is not "failed
  review". Nothing is stored: every read works it out afresh, so the answer
  cannot go stale, and a link starts resolving the moment its target appears
  without the bundle being touched. A citation of a whole OEP dataset resolves
  to the tables that dataset groups _now_ - that currency is the point of
  allowing the coarser citation, and it is why a table citation is the
  reproducible one. A dead link is never removed and never blocks its target's
  deletion, so nobody's citation can hold somebody else's data hostage. A link
  pointing at an address this platform has no route for - the graph holds
  databus URLs - reports nothing rather than reporting "deleted". What gets
  looked up is taken from the link's stored address and never from its label,
  because the older `manage-datasets/` route takes those as two separate values
  and a link can carry a real table's address beside a human-readable title
  [(#2469)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2469)

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

- A whole scenario bundle can now be declared in one call:
  `POST /api/v0/scenario-bundles/<uid>/replace/` takes the complete bundle -
  fields, scenarios, study reports and the dataset links each scenario cites -
  and makes the bundle be exactly that. **This is the only place in the API
  where leaving something out removes it**, which is why it has an address of
  its own rather than being a verb on the bundle's URL, and why it requires the
  version as `If-Match`. What is removed is bounded by type exactly as a
  `DELETE` is: a scenario or a link the payload does not mention goes, while
  regions, contacts, organisations, funders, authors, models, frameworks and
  every picked ontology term are unlinked and never deleted - and anything
  another bundle still points at is kept, with the answer saying which was
  which. Sending back what you read is free: a nested resource that carries the
  `_meta.uid` it was read with keeps its identity, so a re-import updates its
  scenarios instead of recreating them, and a run that declares what is already
  there writes nothing at all - no version bump and no history line. Together
  with `GET /api/v0/scenario-bundles/?acronym=...` this is the whole of an
  idempotent re-import: look it up, create it if it is not there, otherwise
  declare it - a pipeline keeps no state between runs
  [(#2477)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2477)

- A read of a scenario bundle now includes the dataset links of each of its
  scenarios, so what you read is what a write accepts - links were the one part
  of a bundle that a read did not mention, and the new declare-the-whole-bundle
  endpoint would have removed them for that reason alone. A bundle can be
  created with them nested in the same call
  [(#2473)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2473)

- A dataset link can now point somewhere that is not a page on this platform.
  The live knowledge graph holds such links - databus addresses written long
  before this API - and they could be read but not written, so a bundle holding
  one could not be sent back. They now read and write as `ref: "external"` with
  the address in `url`, and every link reports the address it actually stores,
  so a link whose stored address and human-readable title disagree - which the
  older route allowed - survives a round trip pointing where it always did
  [(#2473)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2473)

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

- The tag administration page under Database no longer fails with a server error
  when a tag has an empty identifier. Such tags cannot be created today, but
  older data copied over from the database can contain one, and the page tried
  to link every tag to its editor -- one tag without an address took the whole
  list down for everyone. It is now listed, marked as not editable here, and
  every other tag stays editable. Found on the staging server before release
  [(#2521)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2521)

- Viewing a table in the browser can no longer be refused by the limit on
  database connections. The limit on `/api/v0/advanced` counted every
  connection, including the ones the server opens for a single request and
  closes again when it ends -- which is every search the table view sends, two
  per redraw, and every call to the table REST API. An account paging through a
  couple of tabs was refused, and told about a bug in a library it had never
  used. Now only connections a client opens and keeps across requests
  (`advanced/connection/open`) count. Reaching the limit answers `429` with the
  number of connections and how to close them, and an anonymous caller is told
  that the limit is shared and that logging in gives one of its own. A request
  that waits too long for a free database connection now answers `503` with
  `Retry-After` instead of `400 "Invalid request"`, because a retry may well
  succeed. The limit for anonymous clients, which all of them share, drops from
  15 to 4 in `securitysettings.py.default`. An existing `securitysettings.py` is
  not updated by a deploy and has to be changed by hand
  [(#2492)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2492)

- The limit on how many connections one account may hold open on
  `/api/v0/advanced` now means the number it states. Each request counted the
  account's open connections before registering its own, and nothing kept two
  requests from counting at the same moment -- so requests arriving together
  could each see room and all be let through, and how many were refused depended
  on timing. Counting and taking a place are now one step, and a place is given
  back if the connection then fails to open. The same step stops two requests
  for one connection id from both opening it, where the second used to replace
  the first. This is the second half of the problem the entry below describes.
  The count is kept per server process, so the limit is a true ceiling while
  that part of the API runs in one process
  [(#2492)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2492)

- Two requests arriving at `/api/v0/advanced` at the same moment could answer
  with an internal server error. A connection was entered into the server's list
  of open connections a fraction before it recorded whose it was, and every
  request that reads that list compares owners -- so a connection caught in
  between had no owner to compare against, and the reading request failed
  outright instead of counting it. A connection is now listed only once it is
  complete. This is the first half of the problem: the list is still read
  without a lock, so the count of a user's open connections remains inexact
  [(#2492)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2492)

- A query on the advanced API no longer commits a database connection after it
  has handed that connection back. Connections return to a shared pool as soon
  as a response has been streamed, and a commit issued afterwards landed on
  whichever request held the connection next -- committing that request's
  unfinished work, so its own rollback silently did nothing and a write that
  failed part-way could be kept. It could also break the response it belonged
  to, if the pool had meanwhile discarded the connection. The commit now happens
  while the connection is still held, and every step that runs after a response
  looks the connection up at that moment instead of holding on to one
  [(#2516)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2516)

- An address under `/ontology/` for something the platform does not serve now
  answers "not found". Depending on which address was used, an unknown name
  previously rendered an ontology page for nothing, a search page for nothing,
  or an internal server error. The platform now keeps a list of what it serves
  there, so all three answer the same way -- including when the name is known
  but its files are missing from a deployment, which was the error
  [(#2501)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2501)

- The container stack's Apache configuration is now in the repository. It was
  excluded by an ignore rule meant for a directory of the same name, so the file
  the production image build copies had never been committed -- a build from a
  clean checkout could not have worked. The configuration also gains the
  separate single-process group that the stateful part of the API requires, and
  the request timeouts production runs with
  [(#2495)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2495)

- The platform no longer runs out of database connections. A query that failed
  part-way left its connection checked out for the life of the server process,
  with its transaction still open, so the pool grew by roughly seventeen
  connections a day until the database refused new ones -- at which point
  viewing a table's data, and anything else needing the database, answered
  `{"reason": "Invalid request"}`. Connections are now returned however a query
  ends, and the pool is bounded so it cannot exhaust the database even if
  something else leaks. The limit on simultaneous connections for anonymous API
  clients drops from 40 to 15 to stay inside that bound
  [(#2495)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2495)

- **Security:** queueing a structural change to a table
  (`POST /api/v0/tables/<name>/`) required no authentication — an anonymous
  request was accepted — and the values it carried were written into the
  database by building the SQL statement around them, so a value containing a
  quote could change the statement rather than be stored by it. The endpoint now
  requires write permission on the table, like every other write to it, and both
  queue writers bind their values instead of interpolating them. Changes already
  queued are unaffected in what they contain
  [(#2486)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2486)

- Viewing a table's data no longer fails intermittently with
  `{"reason": "Invalid request"}`. The connection pool to the data database
  discarded a connection for being old but not for being dead, so a connection
  the server had already closed was handed to the next request; the retry worked
  because the pool replaced it by then, which is why reloading appeared to help.
  Connections are now checked before use
  [(#2488)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2488)

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

- Rule 3 of the client guide for scenario bundles described `replace/` as an
  endpoint still being built, with a worked exchange answering `404`. It
  shipped, and it is the one rule on that page about destroying data, so the
  page was telling automation authors that the address where omission deletes
  things cannot be reached yet. The rule is now written in the present tense
  around a real recorded exchange: a declaration that changes a field, adds a
  scenario and leaves the study report out, answered with `_meta.deleted` naming
  the report. It also states the property the replace slice's most important
  test exists for -- a bundle's dataset links are nested under their scenario
  and survive a replace that sends them back, and are deleted by one that does
  not -- and the stale pointer to the closed issue is replaced by the operation
  in the reference, which has been there since `replace/` landed
  [(#2500)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2500)

- Rule 2 of the same page said without qualification that `_meta` is read-only
  and dropped before validation. That stopped being true when `replace/` landed,
  which reads `_meta.uid` on a nested sub-resource to tell which one a
  declaration means. The exception is now named where the rule is stated, with
  the two rules pointing at each other, and it is spelled out that naming is not
  assigning: the identifier is still the server's, a sub-resource naming none is
  created with a fresh one, and one naming an identifier the bundle does not
  hold is refused with nothing written
  [(#2500)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2500)

- A test that pins behaviour a documentation page describes now names that page,
  in its docstring, and a check in the suite fails when a named page is not in
  the tree. The pointer runs from the code to the page rather than the other way
  about: a citation written in prose rots silently on a rename, while a pointer
  in a test is read at the moment somebody changes the behaviour -- the only
  moment the page is wrong. Eleven tests carry one, covering all nine rules of
  the client guide. The one that existed before named a research note in a
  private vault, which nobody outside the project can open, and it was written
  by the very change that left a table in the architecture guide wrong about two
  fields until a reader noticed. The check asserts only that the pages named do
  exist; it does not require a pointer, so a page may describe something no test
  pins yet without turning the suite red
  [(#2462)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2462)

- The reference's sections are checked for dead links on **every** documentation
  page, not only on the reference itself. Two pages had come to cite the
  superseded _Scenario Bundles (legacy)_ section from elsewhere, so renaming it
  would have gone red in one place and quietly dead in two. Doing this found
  that the check also mis-read a citation ending a Markdown link, taking the
  link's own closing bracket for part of the section's name
  [(#2462)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2462)

- The legacy **Edit scenario datasets** page is gone. It documented the singular
  `scenario-bundle/scenario/manage-datasets/` route, which the scenario-bundle
  REST API replaces, and it promised group-based shared editing of a bundle,
  which was ruled out of scope and does not exist. The route itself still works
  and is still described -- in the API Reference, under _Scenario Bundles
  (legacy)_, which names the endpoint that replaces it. Its account of databus
  registration, the only one the documentation carries, moves into **Writing
  scenario bundles** beside the rule about what a dataset link may cite, and now
  says which route can still accept such an address: the superseded one, not the
  new API
  [(#2461)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2461)

- A guide for clients of the scenario-bundle API: **Writing scenario bundles**,
  under Web-API's → Guides. The generated API Reference says what each endpoint
  takes; this page carries the nine rules that decide what a request does and
  that no signature can state — among them that a key left out is left
  untouched, that `_meta` comes back unstripped so a read can be sent back, that
  a create takes nested scenarios where a patch refuses them, that a change is
  refused only for the shape violations it introduces while a create is judged
  whole, and that a successful write can report that its own history entry was
  lost. Each rule carries a real request and response and links the reference at
  the operation it describes. One rule, delete-by-omission on the replace
  endpoint, was written before that endpoint existed and marked as pending
  rather than left out, since a reader who saw the other eight would conclude
  that leaving a key out is always safe; it describes the shipped endpoint as of
  #2500, below
  [(#2460)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2460)

- The API documentation described its OEDB half **twice** — once on the
  generated API Reference and once on the OEDB page, which embedded a separate
  hand-written file. The hand-written one is gone, and everything it described
  is now in the reference, generated from the code: every one of the 107
  operations of `api/v0` says what it does, 66 of them describe the payload they
  take, and none is left to be inferred. The OEDB and OEKG pages are guides now
  — what the endpoints are for and which one to reach for — and link into the
  one reference instead of repeating it
  [(#2454)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2454)

- The eight schema-qualified table addresses
  (`/api/v0/schema/<schema>/tables/…`) are documented as what they are: the
  older spelling of `/api/v0/tables/…`, marked deprecated, with the `<schema>`
  segment described as ignored — it is not read by anything, so any value
  reaches the same table. They had been appearing in the reference with a
  fragment of regular expression where the address should be, which no client
  could call

- The reference's sections are **named and ordered** rather than derived from
  the first segment of each address. Every one of the 107 operations now sits in
  one of thirteen named groups, each carrying a line saying what it holds, and
  the two superseded surfaces say so and name what replaced them: the singular
  `scenario-bundle/scenario/manage-datasets/` route, and the schema-qualified
  table addresses. Before this the group came from the path, so the single
  legacy route and the whole REST API replacing it rendered as adjacent sections
  one letter apart with nothing distinguishing them, and the table endpoints
  were split across two sections by which spelling of their address was used.
  Superseded sections are read last, and the names are stable enough for a
  documentation page to link into a section and stay linked. Operation
  identifiers no longer carry a fragment of regular expression either -- a
  generated client would have held a method named after a character class
  [(#2459)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2459)

- The OEKG page is named for what it documents — the read-only SPARQL endpoint —
  and says where writing to the graph happens instead. It had been titled "OEKG
  API" while describing one endpoint of it. The scenario-dataset page no longer
  escapes that section and appear beside "Architecture" in the top-level
  navigation

- The documentation has an **API Reference** page of its own, listing every
  endpoint of `api/v0` -- the OEDB table and row endpoints, the dataset
  endpoints and the OEKG scenario-bundle endpoints -- in one place. The
  description behind it is generated from the code and committed to the
  repository, so a pull request shows what the description of the API became,
  and a test regenerates it and fails when the committed copy has fallen behind,
  naming the command that brings it back in step. The check validates the
  description before comparing it: a wrong annotation can otherwise produce a
  document that is reproducibly wrong and so passes a comparison forever. The
  OEKG page's own OpenAPI file is retired with it -- it described the SPARQL
  passthrough rather than the endpoints, and that page keeps its SPARQL example
  and now points at the reference for the rest
  [(#2474)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2474)

- That reference now states the scenario-bundle API's contract rather than
  listing its addresses. Every one of the twenty operations describes the
  refusals it can give, the writes declare the `If-Match` header they require
  and the `ETag` that feeds it, `?expand=` appears where it is offered, the
  request payloads come from the serializers that validate them, and the bundle
  read lists the RDF forms it serves. Previously each operation declared `200`
  and nothing else, so a client written from the document would have handled
  none of the refusals it actually meets. Every operation also says in words
  whether it is public or needs a login: the reference page's padlock answers a
  different question -- it closes when a requirement is already met, so public
  reads render locked and writes needing a token render unlocked -- and the
  security declarations behind it are correct and deliberately unchanged. Each
  operation also describes the body it answers with -- the writable payload and
  the read-only `_meta` beside it, the page envelope around a collection, and
  the two lists a delete reports -- and a test validates a real response from
  every endpoint against the description, so a body and the document cannot come
  apart unnoticed
  [(#2475)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2475)

- The OEKG shape guide undercounted the places this repo fetches the ontology
  from: four, where there are five - `podman/entrypoint.sh` was missed. The
  count is the argument for pinning that fetch behind one seam the way the shape
  already is, so the sentence is replaced by a table naming each site, its URL
  and whether it is pinned - one of the five is, and two of the others are the
  same container's build and its entrypoint
  [(#2476)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2476)

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

- The addresses the `oedialect` client depends on are now written down and
  checked. It reaches the platform only through `/api/v0/advanced/`, and until
  now nothing recorded which of those addresses it needs, so renaming or
  removing one would have broken every user of that client without a test
  noticing. Two of the addresses it asks for have in fact never existed; they
  are recorded as such rather than quietly fixed, because whether to serve them
  or drop them from the client is a decision for both projects
  [(#2518)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2518)

- `EXTERNAL_URLS` in the settings listed the same 21 entries twice. Python keeps
  the last of a repeated key, so the duplicates changed nothing - until someone
  edited one of the two copies, at which point which one wins is decided by
  position in the file. The values were identical, so removing the second block
  leaves every link exactly as it was
  [(#2507)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2507)

- The OEKG shape validator merges in only the ontology labels a bundle actually
  names, instead of all 2,054 of them. The label subset is there because the
  shape requires exactly one label on every ontology term a bundle picks, and a
  bundle picks a handful; the rest was copied into every validation and then
  copied again by the validator itself. Same verdicts, and the `oekg` test suite
  -- 45% of the whole run -- does a third of the processor work it used to (184
  s down to 64 s). What is left of a local run is the graph store's own write
  cost, which no change here can reach
  [(#2479)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2479)

- The test run no longer buries itself in debug logging. The shipped
  `securitysettings.py.default` set the root logger to `DEBUG`, which was
  harmless until the OEKG tests began talking to a real graph store over HTTP --
  since then every SPARQL query and update wrote a line, so a continuous
  integration run produced tens of thousands of them and anything worth reading
  was lost among them. The root level is `INFO` and `urllib3` is pinned to
  `WARNING` in its own right, so raising the root back to `DEBUG` to trace our
  own code does not bring the flood back. An existing local
  `securitysettings.py` is not affected and can be updated by hand

- The repair command's tests quiet the rdflib warning they provoke on purpose.
  They write a year-only value typed as a timestamp -- the very defect the
  `year-dates` repair exists for -- and rdflib logged a warning with a traceback
  each time it parsed it, which is on every read. It is silenced where the value
  is written deliberately, so the same warning coming from real data is still
  visible

- Remove `StudyDescriptors.js`, the hardcoded study-descriptor array replaced by
  the OEO-served list. Nothing imported it any more
  [(#2450)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2450)
