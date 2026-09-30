<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# The OEDB REST API

The OEDB is this platform's database of energy data tables. This page explains
what the REST API over it is for and how the pieces fit together. **Every
endpoint is listed in the [API Reference](../api-reference.md)** — that page is
generated from the code, so it is the one to trust about what exists and what
each call takes.

!!! Info "We are still in the process of migrating this document!"

    If you are looking for our former ReadTheDocs based documentation: We do
    not support it anymore and added a redirect to this page here. Migrating
    the outdated documentation and updating the content will take some time.
    Please revisit this page later again.

In the meantime we suggest you to have a look at our Courses & Tutorials
available in the
[Academy](https://openenergyplatform.github.io/academy/tutorials/).

## What the REST API offers

When working with data, it is very helpful to be able to implement programmatic
solutions for managing data resources. The REST API provides such functionality
by opening the underlying database of the OEP website over HTTP. Tables are
addressed by name, and the common JSON format is used to transfer the data, so
an external application can read what is on the platform and upload new data to
it.

## How a table is addressed

**By name, and by name alone.** Table names are global on this platform: no two
tables share one, whichever topic they are published under, so
`/api/v0/tables/<name>/` is the whole address.

You will also see a longer form in older code and older documentation:

```
/api/v0/schema/<schema>/tables/<name>/
```

It still works, and it reaches exactly the same table — but the `<schema>`
segment **selects nothing**. It is not captured by the route, so no value of it
changes where the request goes. It is marked deprecated in the reference for
that reason. Prefer the short form.

## What sits where

|                           |                                                                                                |
| ------------------------- | ---------------------------------------------------------------------------------------------- |
| **A table's structure**   | `/api/v0/tables/<name>/` — its columns, indexes and constraints                                |
| **A table's rows**        | `/api/v0/tables/<name>/rows/` — read, insert, update, delete                                   |
| **A whole CSV at once**   | `/api/v0/tables/<name>/bulk-upload/` — see below                                               |
| **A table's metadata**    | `/api/v0/tables/<name>/meta/` — its OEMetadata document                                        |
| **Datasets**              | `/api/v0/datasets/` — the catalogue entries that group tables                                  |
| **The `advanced/` block** | a thin passthrough to the database, meant to be driven by a client library rather than by hand |

## Creating a table: the one thing to get right

A table is created with `PUT /api/v0/tables/<name>/`, and **the schema it lands
in comes from a query parameter**:

```
PUT /api/v0/tables/<name>/?is_sandbox=true
```

Omit `is_sandbox` and the table is created in the public `data` schema, where
everyone can see it. There is no confirmation step and no way back except
deleting the table, so it is worth sending deliberately.

## Uploading a lot of rows

`POST /api/v0/tables/<name>/bulk-upload/?delimiter=,` takes **the CSV itself as
the request body** — not JSON wrapping one. It appends in a single transaction:
either the whole file lands or none of it does.

Send it gzipped (`Content-Encoding: gzip`) unless the file is small. On a large
upload the platform is not the bottleneck — the client's uplink is — and CSV
compresses well enough to change what is reachable in practice.

## Authentication

Most write endpoints need a token. Register at
<https://openenergyplatform.org/accounts/signup/> or sign in with your
institution, then find your API token on your profile page under the "Settings"
tab.

See the guide on
[how to get started with the OpenEnergyPlatform](https://openenergyplatform.github.io/academy/courses/02_start/#how-do-i-get-started-with-the-oep).
