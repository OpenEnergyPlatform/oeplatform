<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Ontop Service Configuration

This directory contains the production configuration for the Ontop SPARQL
endpoint. Two files must be provided manually before building or starting the
ontop service — they are gitignored and must never be committed.

## Required files (not in git)

### 1. `postgresql.jar` — JDBC driver

Download the PostgreSQL JDBC driver from <https://jdbc.postgresql.org/> and
place it here as `postgresql.jar`.

This file is copied into the ontop image at build time:

```sh
# Build from the repository root after placing the jar here
podman build -t localhost/oep-ontop:latest -f docker/Dockerfile.ontop docker/
```

> The `Dockerfile.ontop` copies the jar from `docker/serviceConfigs/ontop/`, not
> from this directory. Place a copy (or symlink) there too before building.

### 2. `ontology.owl` — Open Energy Ontology

Download the latest OEO build artefacts from the
[OEO GitHub releases](https://github.com/OpenEnergyPlatform/ontology/releases/latest)
and place the `ontology.owl` file here.

```sh
wget -O /tmp/oeo.zip \
    https://github.com/OpenEnergyPlatform/ontology/releases/latest/download/build-files.zip
unzip -j /tmp/oeo.zip "*/ontology.owl" -d podman/serviceConfigs/ontop/
rm /tmp/oeo.zip
```

## Files in git

| File                        | Description                                             |
| --------------------------- | ------------------------------------------------------- |
| `mapping.obda`              | Empty OBDA mapping skeleton — extend for your tables    |
| `ontop.properties.template` | JDBC connection template — copy and fill in credentials |

### `ontop.properties` credentials

`ontop.properties` is gitignored. Create it from the template and fill in the
real credentials from your `.env` / `oep.env` file:

```sh
cp podman/serviceConfigs/ontop/ontop.properties.template \
   podman/serviceConfigs/ontop/ontop.properties
# then edit ontop.properties — it must never be committed
```

```properties
jdbc.user=REPLACE_WITH_POSTGRES_USER      # → value of POSTGRES_USER
jdbc.password=REPLACE_WITH_POSTGRES_PASSWORD  # → value of POSTGRES_PASSWORD
```

Ontop does not support environment variable substitution in this file, so
credentials must be written in plain text. The `.gitignore` in this directory
prevents accidental commits.

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
