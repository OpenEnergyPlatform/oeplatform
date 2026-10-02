<!--
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Ontop

!!! info "You are here"

    Step 3 of the **Production deployment (Podman)** guide, after
    **[Install](install.md)**. This page covers the ontop service end to end — how
    it provisions itself, and the **repeatable** procedure for applying a real
    mapping. Next comes **Update**.

**Ontop** exposes the relational OEDB as a SPARQL endpoint — a _Virtual
Knowledge Graph_. It answers SPARQL queries by translating them to SQL against
Postgres, using a **semantic mapping** from tables to RDF. It is the enabling
technology for querying OEDB content as linked data (e.g. quantitative scenario
comparison).

This is the **one** page for everything ontop: the install-time bits are
automatic, and the recurring bit — applying/updating a mapping — is a procedure
you run whenever the mapped tables or the mapping itself change.

## Install-time: it provisions itself

The ontop image
([`docker/Dockerfile.ontop`](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/docker/Dockerfile.ontop))
bakes in everything it needs, so there are **no files to place by hand**:

- **PostgreSQL JDBC driver** — downloaded from Maven Central at build time and
  put on Ontop's classpath. Pin a version with a build-arg (default `42.7.3`):

  ```sh
  podman build --build-arg JDBC_VERSION=42.7.3 \
    -t localhost/oep-ontop:latest \
    -f docker/Dockerfile.ontop docker/
  ```

- **Ontology** — baked in at `/opt/ontop-config/ontology.owl`
  (`ONTOP_ONTOLOGY_FILE`).
- **Mapping** — an **empty** default is baked in at
  `/opt/ontop-config/mapping.obda` (`ONTOP_MAPPING_FILE`), so the endpoint
  **always starts cleanly**, even before the OEDB data tables exist.
- **DB connection** — supplied at runtime from `oep.env`; Ontop reads these
  natively, so there is **no `ontop.properties` file** to write:

  ```sh
  ONTOP_DB_URL=jdbc:postgresql://postgres:5432/oedb
  ONTOP_DB_USER=<db-user>
  ONTOP_DB_PASSWORD=<db-password>
  ```

The endpoint runs with `ONTOP_LAZY_INIT=true`, so it comes up even before the
mapped source tables exist; mapping errors then surface at **query time** rather
than blocking startup. This is why install can complete with an empty mapping
and you apply the real one later.

## Recurring: apply or update a real mapping

Do this **once the source tables exist** in the `oedb` database, and again
**whenever the mapping or the underlying tables change**. It is a repeatable
procedure, not a one-off.

A mapping entry looks like:

```obda
[MappingDeclaration] @collection [[

mappingId       my_table_TargetClass
target          oekg:data-descriptor/my_table/{id} a oeo:IAO_0000027 .
source          SELECT "id" FROM "data"."my_table"

]]
```

Choose one of two ways to apply it:

=== "Override at runtime (recommended while evolving)"

    No rebuild. Provide your mapping to the running container and restart:

    - bind-mount your file over `/opt/ontop-config/mapping.obda`, **or**
    - point `ONTOP_MAPPING_FILE` at a mounted file.

    Then restart the service so Ontop reloads:

    ```sh
    systemctl --user restart oep-ontop
    ```

    This is best while the mapping is still changing often — you iterate without
    rebuilding the image.

=== "Bake it in (for a stable mapping)"

    Replace the empty default the image ships
    (`docker/serviceConfigs/ontop/mapping.default.obda`) with your real
    `docker/serviceConfigs/ontop/mapping.obda`, rebuild, and restart:

    ```sh
    podman build -t localhost/oep-ontop:latest -f docker/Dockerfile.ontop docker/
    systemctl --user restart oep-ontop
    ```

    This is best once the mapping has stabilised — it travels with the image.

!!! note "Reloading is a restart"

    Ontop loads the mapping at startup, so applying a changed mapping means
    **restarting the ontop service**. There is no live hot-reload in this setup.

## Verify

- `systemctl --user status oep-ontop` — `active (running)`.
- The Ontop SPARQL UI/endpoint answers a trivial query.
- If a query errors, it is usually a mapping/table mismatch (surfaced lazily) —
  check the logs: `journalctl --user -u oep-ontop -f`.

---

**Next → [Update](update.md)** — deploying a new release of the platform.
