<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Ontop Service Configuration

The ontop service is **self-provisioning** — you do not need to place any files
here to run it. The ontop image
([docker/Dockerfile.ontop](../../../docker/Dockerfile.ontop)) bakes in
everything it needs:

- **PostgreSQL JDBC driver** — downloaded from Maven Central at image build
  time.
- **`ontology.owl`** — baked into the image at `/opt/ontop-config/ontology.owl`.
- **`mapping.obda`** — an **empty** default mapping is baked in at
  `/opt/ontop-config/mapping.obda`, so the endpoint starts cleanly even before
  the OEDB data tables exist. Provide the real mapping only once the tables are
  present (see below).
- **DB connection** — supplied at runtime via the env vars `ONTOP_DB_URL`,
  `ONTOP_DB_USER` and `ONTOP_DB_PASSWORD`.

The database connection is configured like everything else — through `oep.env`
(quadlets) or `.env` (compose). Ontop reads these environment variables
natively, so there is **no `ontop.properties` file** to create.

```sh
# oep.env / .env
ONTOP_DB_URL=jdbc:postgresql://postgres:5432/oedb
ONTOP_DB_USER=<postgres user>
ONTOP_DB_PASSWORD=<postgres password>
```

## `mapping.obda`

The image ships an **empty** mapping so it always starts. The real mapping
(`docker/serviceConfigs/ontop/mapping.obda`) should be applied only once the
source tables exist in the `oedb` database. Two ways to apply it:

1. **Override at runtime** (no rebuild): bind-mount your mapping over
   `/opt/ontop-config/mapping.obda`, or point `ONTOP_MAPPING_FILE` at a mounted
   file. This is the recommended approach while the mapping is still evolving.
2. **Bake it in**: replace the empty default in `docker/Dockerfile.ontop`
   (`mapping.default.obda`) with `mapping.obda` and rebuild the image.

Extend the mapping as needed:

```obda
[MappingDeclaration] @collection [[

mappingId       my_table_TargetClass
target          oekg:data-descriptor/my_table/{id} a oeo:IAO_0000027 .
source          SELECT "id" FROM "data"."my_table"

]]
```

The endpoint starts with `ONTOP_LAZY_INIT=true`, so it comes up even before the
mapped source tables exist in the `oedb` database; mapping errors then surface
at query time rather than blocking startup.
