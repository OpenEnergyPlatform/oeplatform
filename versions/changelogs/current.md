<!--
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2026 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

## Features

## Bugs

- Model/Framework factsheets: the tag editor no longer attaches every tag on the
  platform. Opening a factsheet for editing pre-checked all ~825 tags and showed
  them as already attached, so saving attached the lot - one database query per
  tag, which is what made "submit all" take minutes. The editor now shows only
  the tags that factsheet actually has, saving attaches exactly what was
  selected, and a save that fails validation comes back with the selection
  intact instead of discarding it. A save no longer wipes a factsheet's tags
  when the form is submitted without the tag widget. New: a "remove all tags"
  button and a live count of the selection on the Tags tab.
  [(#2385)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2385)
  [(#2381)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2381)

- Model/Framework factsheet overview: the sidebar tag filter now lists each tag
  actually in use by that sheet type exactly once, in name order, instead of one
  checkbox per tag _attachment_ - on production 12,156 checkboxes for 825
  distinct tags, 6 MB of the page. The frameworks page previously offered 290
  tags where only 71 were in use, so 219 of its checkboxes returned no results
  when clicked.
  [(#2346)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2346)

- Model/Framework factsheet overview: the active tag filter is now kept in the
  page URL (`?tags=<tag>,<tag>`), so a filtered view can be reloaded, bookmarked
  and shared, and returning to such a URL restores the checked tags. This also
  fixes the "Download CSV" link silently returning a file with only a header row
  whenever a tag filter was applied: the page sent a prefixed value the download
  endpoint did not recognise, so it matched nothing and reported no error. Links
  in the old format keep working.
  [(#2346)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2346)

- Deleting a Model/Framework factsheet is now restricted to administrators, and
  refused by the server rather than only hidden in the page. The delete button
  and the edit link were rendered on every factsheet page with no permission
  check at all, so any registered account could irreversibly destroy any of the
  339 factsheets in one click, with no record of who did it. Anonymous visitors
  are no longer shown edit and delete buttons they cannot use. Editing stays
  open to every logged-in account, as intended. Every factsheet create, update
  and delete now leaves one structured log line.

- Model/Framework factsheet overview: the table's row data is now built by the
  server in one pass instead of being assembled in the page template, which
  takes the page from 2,138 database queries to 3 regardless of how many
  factsheets exist. The template emitted each row's name and tag list once per
  field group - seven times per model factsheet - so the page carried 85,092 tag
  entries for 12,156 actual tag attachments; duplicate entries overwrote each
  other in the browser, which is why this was never visible. The data is also
  now delivered as JSON rather than as generated JavaScript, so a factsheet
  whose text happens to contain a closing script tag can no longer break the
  page. [(#2346)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2346)

- Model/Framework factsheet overview: the page now sends the columns the table
  actually shows - eight of 173 for models, five of 43 for frameworks - instead
  of every field of every factsheet, which on production is a 20 MB page to
  display eight columns. The remaining columns are fetched once, in the
  background, the first time a column is switched on or the search box is used,
  so searching still matches text in hidden columns and a visitor who does
  neither never waits for them. Sorting, paging, the tag filter and the CSV
  download are unchanged.
  [(#2346)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2346)

## Documentation updates

## Code Quality
