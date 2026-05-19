<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Podman Usage

> Tested on Linux with rootless Podman. Requires `podman` and `podman-compose`.

This directory contains the Podman-based production deployment for OEPlatform.
All application code and static assets are baked into the container images at
build time — no bind mounts are used.

## Prerequisites

- [Podman](https://podman.io/getting-started/installation) ≥ 4.0
- [podman-compose](https://github.com/containers/podman-compose) ≥ 1.0
- Rootless Podman configured (`/etc/subuid` and `/etc/subgid` entries for your
  user)

Install podman-compose (if not already installed):

```sh
pip install podman-compose
# or via your distro's package manager, e.g.:
# dnf install podman-compose   (Fedora/RHEL)
# apt install podman-compose   (Debian/Ubuntu)
```

## Services

| Service      | Description                           | Default port |
| ------------ | ------------------------------------- | ------------ |
| `postgres`   | PostgreSQL with pre-seeded OEP schema | 5432         |
| `fuseki`     | Apache Jena Fuseki triple store       | 3030         |
| `oeplatform` | OEP web app (Apache2)                 | 8080         |
| `ontop`      | Ontop SPARQL endpoint                 | 8081         |
| `lookup`     | DBpedia Lookup service                | 3004         |

## Start the Stack

Run all commands from the **repository root**.

```sh
podman-compose -f podman/podman-compose.yaml up -d
```

## Stop the Stack

```sh
podman-compose -f podman/podman-compose.yaml down
```

## Override Ports

Default ports can be changed via environment variables before starting:

```sh
export OEP_PORT_WEB=9090
export OEP_PORT_POSTGRES=5433
```

## View Logs

```sh
podman-compose -f podman/podman-compose.yaml logs -f oeplatform
```

## Open a Shell

```sh
podman exec -it oeplatform bash
```

## Reset Database

```sh
podman-compose -f podman/podman-compose.yaml down
podman volume rm podman_pgdata   # check exact name with: podman volume ls
podman-compose -f podman/podman-compose.yaml up -d
```

The postgres container recreates all tables on a fresh volume automatically.
