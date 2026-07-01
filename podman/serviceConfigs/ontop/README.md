<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Ontop Service Configuration

This directory is mounted **read-only** into the ontop container at
`/opt/ontop-config` and supplies its **runtime configuration**. Two files here
must be provided manually before starting the service — they are gitignored and
must never be committed.

## Required runtime files (not in git)

### 1. `ontology.owl` — Open Energy Ontology

Download the latest OEO build artefacts from the
[OEO GitHub releases](https://github.com/OpenEnergyPlatform/ontology/releases/latest)
and place the `ontology.owl` file here.

```sh
wget -O /tmp/oeo.zip \
    https://github.com/OpenEnergyPlatform/ontology/releases/latest/download/build-files.zip
unzip -jo /tmp/oeo.zip "*/ontology.owl" -d podman/serviceConfigs/ontop/
rm /tmp/oeo.zip
```

### 2. `ontop.properties` — JDBC connection + credentials

Create it from the template and fill in the real credentials from your `.env` /
`oep.env` file:

```sh
cp podman/serviceConfigs/ontop/ontop.properties.template \
   podman/serviceConfigs/ontop/ontop.properties
# then edit ontop.properties — it must never be committed
```

```properties
jdbc.user=REPLACE_WITH_POSTGRES_USER          # → value of POSTGRES_USER
jdbc.password=REPLACE_WITH_POSTGRES_PASSWORD  # → value of POSTGRES_PASSWORD
```

Ontop does not support environment variable substitution in this file, so
credentials must be written in plain text. The `.gitignore` in this directory
prevents accidental commits.

## The PostgreSQL JDBC driver lives elsewhere

The `postgresql.jar` driver is **not** used from this directory. It is baked
into the ontop image at **build time** from `docker/serviceConfigs/ontop/` —
[docker/Dockerfile.ontop](../../../docker/Dockerfile.ontop) copies it to
`/opt/ontop/lib/postgresql.jar`. Place it there before building the image:

```sh
# From the repository root
curl -fsSL \
  "https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar" \
  -o docker/serviceConfigs/ontop/postgresql.jar

podman build -t ghcr.io/openenergyplatform/oeplatform-ontop:latest \
  -f docker/Dockerfile.ontop docker/
```

That path is gitignored (`**/serviceConfigs/ontop/postgresql.jar` in the root
`.gitignore`), so the driver never enters the repository.

## Files in git

| File                        | Description                                             |
| --------------------------- | ------------------------------------------------------- |
| `mapping.obda`              | Empty OBDA mapping skeleton — extend for your tables    |
| `ontop.properties.template` | JDBC connection template — copy and fill in credentials |

### `mapping.obda` — extending the mapping

The skeleton file contains only prefix declarations and an empty mapping
collection. Add OBDA mappings as needed:

```obda
[MappingDeclaration] @collection [[

mappingId       my_table_TargetClass
target          oekg:data-descriptor/my_table/{id} a oeo:IAO_0000027 .
source          SELECT "id" FROM "data"."my_table"

]]
```

The source table must exist in the `oedb` database before Ontop can start
successfully with a mapping that references it.
