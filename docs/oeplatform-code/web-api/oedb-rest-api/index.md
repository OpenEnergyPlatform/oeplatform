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

|                            |                                                                                                |
| -------------------------- | ---------------------------------------------------------------------------------------------- |
| **A table's structure**    | `/api/v0/tables/<name>/` — its columns, indexes and constraints                                |
| **A table's rows**         | `/api/v0/tables/<name>/rows/` — read, insert, update, delete                                   |
| **A whole CSV at once**    | `/api/v0/tables/<name>/bulk-upload/` — see below                                               |
| **A table's metadata**     | `/api/v0/tables/<name>/meta/` — its OEMetadata document                                        |
| **Who holds a role on it** | `/api/v0/tables/<name>/permissions/` — see below                                               |
| **Datasets**               | `/api/v0/datasets/` — the catalogue entries that group tables                                  |
| **The `advanced/` block**  | a thin passthrough to the database, meant to be driven by a client library rather than by hand |

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

## Sharing a table

`GET /api/v0/tables/<name>/permissions/` lists the users and organizations
holding a role on the table. A Table admin adds one with `POST` to the same
address (`{"user": "<name>", "level": 4}` or
`{"organization": <id>, "level": 4}`), and changes or removes one at
`permissions/user:<id>/` or `permissions/org:<id>/` with `PATCH` or `DELETE`.
The rules are the same as on the table's access drawer and permission page:
Admin goes to users only, an organization stops at Data maintainer and is shared
only by its members, and a table always keeps a user with direct Admin (or,
where it has none, its last Admin grant of any kind).

A change that takes **your own** Admin, or all your access, away is answered
`409` with `"code": "confirmation_needed"` and writes nothing. Send the same
request again with `"confirm": true` in the `PATCH` body, or `?confirm=true` on
the `DELETE`. A `409` with `"code": "last_admin"` cannot be confirmed: give
someone else Admin first.

### Many tables, one organization

`POST /api/v0/organizations/<id>/table-permissions/share/` with
`{"tables": ["<name>", ...], "level": 4}` shares every table named with one of
your organizations, at Data editor (`4`) or Data maintainer (`8`).
`POST /api/v0/organizations/<id>/table-permissions/remove/` with
`{"tables": [...]}` takes the organization's role away again. You need Table
admin on every table named; a table where you are not answers `403` with the
tables in `tables`, and nothing is written. Each request is all or nothing,
takes at most 2,500 tables, and answers with what it `changed` (before and
after, per table) and what it left `unchanged`:

- a share only ever raises a role: where the organization already holds that
  role or more, the table stays as it is;
- a removal leaves a table where the organization holds no role unchanged, so
  sending it again succeeds;
- a removal that would leave a table with no Admin at all, because the
  organization's old Admin grant is its only one, answers `409` with
  `"code": "last_admin"`; one that takes your own access or Admin away answers
  `409` with `"code": "confirmation_needed"` naming them in `tables`; send those
  names back as `"confirm"` (or `true` for any).

## Authentication

Most write endpoints need a token. Register at
<https://openenergyplatform.org/accounts/signup/> or sign in with your
institution, then find your API token on your profile page under the "Settings"
tab.

See the guide on
[how to get started with the OpenEnergyPlatform](https://openenergyplatform.github.io/academy/courses/02_start/#how-do-i-get-started-with-the-oep).
