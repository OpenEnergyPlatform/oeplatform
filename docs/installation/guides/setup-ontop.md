<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Setup ontop service

!!! info "This page has moved"

    The Ontop service is now documented canonically on the
    **[Ontop page of the Production deployment (Podman) guide](../production-podman/ontop.md)**.
    That page covers the whole lifecycle in one place.

The ontop service enables **SPARQL queries over the SQL database** using a
semantic mapping — the enabling technology for quantitative scenario comparison.

The image is **self-provisioning**: the PostgreSQL JDBC driver, the ontology and
an empty default mapping are all baked in at build time, and the database
connection comes from environment variables (`ONTOP_DB_URL` / `ONTOP_DB_USER` /
`ONTOP_DB_PASSWORD`). **Nothing needs to be downloaded or placed manually.** Pin
a different JDBC version at build time with `--build-arg JDBC_VERSION=x.y.z`
(default `42.7.3`).

➡️ **Full documentation — self-provisioning, the `JDBC_VERSION` build-arg, and
the repeatable procedure for applying a real mapping — is on the
[canonical Ontop page](../production-podman/ontop.md).**
