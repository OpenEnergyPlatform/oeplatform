"""The names the reference's groups carry, and the order they are read in.

Swagger draws one accordion per tag and orders them by the document's own tag
list, so these names are what a reader navigates by and what a prose page links
to. Left to itself the generator derives a tag from the first path segment,
which produced two problems this module exists to fix:

- **A path-derived name is not a domain name.** `scenario-bundle` and
  `scenario-bundles` rendered as adjacent accordions one letter apart with
  nothing saying that the first is a single legacy route and the second the
  entire REST API that replaces it. The same split ran through the OEDB half,
  where `tables` and `schema` are the same eighteen operations at two
  spellings of the address.
- **A path-derived name moves when a route moves**, so no page could link into
  the reference and stay linked.

Two conventions, so a reader can tell the two kinds of group apart at a glance:

- **A colon names a sub-group** of the one before it -- `Advanced: Cursor` is
  part of `Advanced`, `Tables: metadata` part of `Tables`.
- **Parentheses mark a superseded surface**, and its description names what
  replaced it. Those groups sort last, so the way in is never the way out.

This module holds data and imports nothing, deliberately: ``oeplatform.settings``
reads ``TAGS`` from here at settings-import time, which is before Django's app
registry exists, and the annotations in ``api.views`` and
``oekg.api_description`` read the names from the same place, so a group's name
is one string rather than one per call site.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

TABLES = "Tables"
TABLE_METADATA = "Tables: metadata"
DATASETS = "Datasets"
SCENARIO_BUNDLES = "Scenario Bundles"
ADVANCED = "Advanced"
ADVANCED_CONNECTION = "Advanced: Connection"
ADVANCED_CURSOR = "Advanced: Cursor"
ADVANCED_TWO_PHASE = "Advanced: Two phase"
OEKG_SPARQL = "OEKG SPARQL"
FACTSHEETS = "Factsheets"
API_DESCRIPTION = "API description"

#: The superseded groups. Both are still routed and still work; both have a
#: replacement in this same document, and their descriptions name it.
SCENARIO_BUNDLES_LEGACY = "Scenario Bundles (legacy)"
TABLES_LEGACY = "Tables (legacy addresses)"

#: The document's tag list, in the order the accordions appear. The order is a
#: reading order rather than an alphabet: what a client publishing data needs
#: first, then the catalogue it lands in, then the knowledge graph, then the
#: session-based interface for clients that drive the database directly, then
#: the small auxiliary endpoints -- and the superseded groups last.
TAGS = [
    {
        "name": TABLES,
        "description": (
            "Create a table, alter its columns and constraints, write and "
            "read its rows, publish it to a topic, and list the tables a topic "
            "holds. **Table names are global**: a table is addressed by name "
            "alone and no two tables share one, whichever topic they are "
            "published under. One listing here is addressed under `datasets/` "
            "and belongs to this group rather than to **Datasets**, because "
            "what it returns is tables: `datasets/list_all/scenario/`."
        ),
    },
    {
        "name": TABLE_METADATA,
        "description": (
            "The OEMetadata document a table carries. Writing it never changes "
            "a row, and a table created without one is given a minimal "
            "document generated from its columns."
        ),
    },
    {
        "name": DATASETS,
        "description": (
            "The catalogue entries that group tables. A dataset's `resources` "
            "are assembled from its member tables when it is read rather than "
            "stored, so a dataset never reports a resource it no longer holds."
        ),
    },
    {
        "name": SCENARIO_BUNDLES,
        "description": (
            "The OEKG scenario bundles as a REST API: a bundle, the scenarios "
            "and study reports below it, the datasets a scenario cites, and "
            "the record of every change. Reads are public; a write needs a "
            "token, and every write to a bundle that already exists carries "
            "`If-Match` -- there is no opt-out."
        ),
    },
    {
        "name": ADVANCED,
        "description": (
            "A thin authenticated passthrough to the database, meant to be "
            "driven by a client library rather than by hand. A call carrying "
            "no session identifiers runs and commits on its own."
        ),
    },
    {
        "name": ADVANCED_CONNECTION,
        "description": (
            "Opening, committing, rolling back and closing the database "
            "session that the other `advanced/` calls are threaded onto."
        ),
    },
    {
        "name": ADVANCED_CURSOR,
        "description": (
            "Cursors inside such a session, and fetching rows from them one at "
            "a time or all at once."
        ),
    },
    {
        "name": ADVANCED_TWO_PHASE,
        "description": (
            "Two-phase commit across a session: begin, prepare, commit, roll "
            "back, and recover the transactions left prepared."
        ),
    },
    {
        "name": OEKG_SPARQL,
        "description": (
            "One read-only SPARQL endpoint against the Open Energy Knowledge "
            "Graph. Anything that would update or delete is refused, whatever "
            "the caller's permissions."
        ),
    },
    {
        "name": FACTSHEETS,
        "description": (
            "The model and framework factsheets held in this platform's own "
            "database. Not the OEKG scenario bundles: the two share the word "
            "*factsheet* and a URL prefix in the web interface, and nothing "
            "else."
        ),
    },
    {
        "name": API_DESCRIPTION,
        "description": (
            "The machine-readable description of `api/v0`: one endpoint, and "
            "the source this page is rendered from."
        ),
    },
    {
        "name": SCENARIO_BUNDLES_LEGACY,
        "description": (
            "**Superseded by Scenario Bundles.** One RPC route that attaches "
            "datasets to a scenario, kept because clients call it. It writes "
            "predicates the canonical shape does not validate, and it is the "
            "singular `scenario-bundle/` address -- one letter from the plural "
            "that replaces it. New clients want `POST "
            "/api/v0/scenario-bundles/{uid}/scenarios/{sid}/datasets/`."
        ),
    },
    {
        "name": TABLES_LEGACY,
        "description": (
            "**Superseded by Tables.** The older schema-qualified spelling of "
            "every endpoint under **Tables**, reaching the same views. The "
            "`{schema}` segment is not captured by the route and therefore "
            "selects nothing: table names are global, so the table is found by "
            "name alone whatever is sent here."
        ),
    },
]
