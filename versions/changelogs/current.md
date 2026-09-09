<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

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

- New management command `repair_factsheet_tags` repairs the factsheets the old
  tag editor damaged - on production 23 of 339 carry a copy of the whole tag
  table, holding 95% of all factsheet tag assignments. It reports by default and
  changes nothing without `--apply`, writes a JSON record of what it removed,
  flags borderline factsheets for a human decision, and dates each factsheet's
  damage so it is possible to say which backup would still recover its real
  tags. Repaired factsheets are set to zero tags; that loss is deliberate and
  recorded.
  [(#2385)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2385)

## Bugs

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
  when no store is reachable.

- `python manage.py fetch_oekg_shapes` obtains the canonical OEKG SHACL shape
  from a pinned revision of the `oekg` repository, and generates the
  `rdfs:label` subset validation needs from the OEO release already on disk.

- The OEKG SPARQL endpoint test patched `oekg.utils.execute_sparql_query` while
  the view binds that function into its own namespace, so the mock never took
  effect and the test made a real network call to a host that only resolves
  inside the compose network. It failed on every local run. Patched at the right
  name, it is now hermetic.

## Documentation updates

- New feature documentation for Model/Framework factsheets on mkdocs: what the
  pages do and who may do what, plus an architecture page recording how the list
  page is built, the release order for the tag repair, and the test seams.

## Code Quality
