<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Web API´s

This section describes the web APIs provided by the oeplatform: HTTP interfaces
that take a JSON request body and answer with a JSON one.

There is **one API**, `api/v0`, and it covers two kinds of thing: the OEDB — the
data tables users upload and the datasets that group them — and the OEKG, the
knowledge graph of scenario bundles.

**One page describes every endpoint of it.** The
[API Reference](./api-reference.md) is generated from the code and checked
against it by the test suite, so it is the page to trust about what exists, what
a call takes and what it can answer.

The guides beside it do the other job — what the endpoints are _for_, which one
to reach for, and the handful of things that catch people out. They link into
the reference rather than repeating it:

- [Working with the OEDB](./oedb-rest-api/index.md) — how a table is addressed,
  creating one, and uploading a lot of rows at once.
- [Database table sizes](./oedb-rest-api/resource-data-size.md) — asking how
  much storage a table takes.
- [Querying the OEKG with SPARQL](./oekg-api/index.md) — the read-only graph
  endpoint, and where writing to the graph happens instead.
