<!--
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Model & Framework Factsheets

A **factsheet** describes a piece of energy system analysis software in a
structured way: what it is for, who maintains it, how open it is, what it can
represent, and how it is validated. There are two kinds, and they are the same
form with different questions:

- a **Model Factsheet** describes a model (171 fields),
- a **Framework Factsheet** describes a modelling framework (41 fields).

Both are browsable at `/factsheets/models/` and `/factsheets/frameworks/`, and
both are open for anyone to read.

!!! warning "The word "factsheet" means two unrelated things on this platform"

    `/factsheets/models/` and `/factsheets/frameworks/` are the **`modelview`**
    Django app, stored in PostgreSQL. `/factsheets/main` and `/factsheets/id/…`
    are **scenario bundles** in the [`factsheet`
    app](../scenario-bundles/index.md), stored in the Open Energy Knowledge
    Graph. They share a URL prefix and nothing else. A scenario bundle *links
    to* a model factsheet; it is not one.

## What a visitor can do

**Browse and filter.** Each overview is one sortable, searchable table. The
sidebar offers the tags actually in use by that sheet type, and selecting more
than one narrows to the factsheets carrying _all_ of them. The active filter
lives in the page address (`?tags=<tag>,<tag>`), so a filtered view can be
reloaded, bookmarked and shared.

**Choose columns.** The table shows eight columns by default and can show all of
them. The sidebar's field groups switch the rest on.

**Download.** "Download CSV" returns the full records as a file, and respects
the tag filter currently applied.

## What a logged-in user can do

**Create and edit.** Any logged-in account may create a factsheet and edit any
factsheet. This is deliberate: community contribution is the intent, and there
is no ownership model.

**Tag.** The editor's Tags tab offers the platform's tags with a live count of
the selection and a "remove all tags" button. Tags are **one vocabulary shared
with database tables** — see [Tags](#tags-are-shared-with-the-database) below.

**Delete, for one week.** Any logged-in account may delete a factsheet for
**seven days after it was created**; administrators may delete at any time.

!!! danger "Deleting is final"

    This part of the platform keeps no history. A deleted factsheet cannot be
    restored, and the log line the deletion leaves records *who* removed *which
    factsheet* — never what it contained. The seven-day window also depends on
    the factsheet's **age**, not on who created it: during that week, any
    logged-in account can delete it, not only its author.

    Factsheets created before this window was introduced are
    administrator-only, permanently.

## Tags are shared with the database

There is one tag vocabulary on the platform. The same `Tag` is attached to
database tables and to factsheets, so renaming or deleting one affects both
sides. Tags are administered at
[`/database/tags/`](https://openenergyplatform.org/database/tags/), reachable
from the Database topic list and from the tag filter on either factsheet
overview. That page reports, before you delete a tag, how many tables **and**
how many factsheets would lose it.

Only administrators may delete a tag.

## Where the code lives

| Concern                                                   | Module                                    |
| --------------------------------------------------------- | ----------------------------------------- |
| Views (list, detail, add/edit, delete, CSV, lazy payload) | `modelview/views.py`                      |
| The 192-column models and the delete rule                 | `modelview/models.py`                     |
| Field groups, defaults, POST handling                     | `modelview/helper.py`                     |
| The table's row payload                                   | `modelview/list_payload.py`               |
| Tag filter and lazy column loading (browser)              | `modelview/static/modelview/`             |
| Tag vocabulary administration                             | `dataedit/views.py`, `dataedit/helper.py` |

For how the list page is built and why, see the
[architecture notes](architecture.md).
