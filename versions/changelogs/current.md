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

- New management command `repair_factsheet_tags`, which repairs the factsheets
  the old tag editor damaged: 23 of 339 on production carry a copy of the whole
  tag table, and those 23 hold 95% of every factsheet tag assignment in the
  database. It reports by default and only changes anything with `--apply`,
  writes a JSON record of exactly which tags it removed from which factsheet,
  prints factsheets that sit near the threshold as needing a human decision, and
  dates each factsheet's damage against the tag table's own history so it is
  possible to say which backup would still recover its real tags. Repairing a
  factsheet sets it to zero tags: the handful of genuine tags it had are
  indistinguishable from the damage, and that loss is deliberate and recorded.
  [(#2385)](https://github.com/OpenEnergyPlatform/oeplatform/issues/2385)

- The tag pages under Database now work as one screen: the create/edit form
  opens beside the tag list instead of on a page of its own with no heading and
  a "Cancel" that led somewhere unrelated, and a name the platform rejects comes
  back with what you typed instead of sending you away empty-handed. Tags are
  one vocabulary shared by database tables and by Model/Framework factsheets,
  and the form now says so: it reports how many tables and how many factsheets
  carry a tag before you delete it. Three defects went with it - deleting a tag
  was possible for any logged-in account (and the button was shown to nobody,
  not even administrators); creating a tag whose name matched an existing one
  apart from capitalisation or punctuation silently renamed and recoloured that
  existing tag everywhere it was used; and a single tag with an unusual internal
  name made the whole overview page fail to load.

- The Database topic list and the Model/Framework factsheet overview now link to
  the tag pages, which nothing on the platform linked to before - they were
  reachable only by typing the address.

- Deleting a Model/Framework factsheet is possible for any logged-in account for
  **one week after the factsheet was created**, and for administrators at any
  time. This gives whoever has just added a duplicate or a test entry a way to
  remove it without finding an administrator. Note what the window does and does
  not say: it depends on the factsheet's age, not on who created it, so during
  that week any logged-in account can delete it - and a deleted factsheet cannot
  be restored, because this part of the platform keeps no history. The 339
  factsheets that already existed are not affected and stay administrator-only.

## Documentation updates

## Code Quality
