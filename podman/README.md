<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Podman Usage

> Rootless Podman deployment for OEPlatform. All application code and static
> assets are baked into the images at build time — no bind mounts.

**📖 Production = Quadlets.** The supported production path is the systemd
**Quadlets** setup, fully documented in the project docs under **Production
deployment (Podman)**
([`docs/installation/production-podman/`](../docs/installation/production-podman/index.md))
— that guide is the source of truth (install, HTTPS, Ontop, update,
maintenance). A quickstart also lives in
[`quadlets/README.md`](quadlets/README.md).

The `podman-compose` path below is a **convenience for local/experimental runs
only** — not the production path.

## Prerequisites

- [Podman](https://podman.io/getting-started/installation) (≥ 4.4 recommended;
  the compose notes below cover older 3.x setups)
- Rootless Podman configured (`/etc/subuid` and `/etc/subgid` entries for your
  user)
- For the compose path:
  [podman-compose](https://github.com/containers/podman-compose)
  (`pip install podman-compose` — the Ubuntu 22.04 apt package is too old)

## Local/dev via podman-compose

```sh
cp podman/.env.example podman/.env      # then fill in all values (gitignored)
podman-compose --env-file podman/.env -f podman/podman-compose.yaml up -d
```

Stop with `... down`; view logs with `... logs -f oeplatform` (or
`podman logs -f oeplatform`); open a shell with
`podman exec -it oeplatform bash`.

The `.env` keys mirror the Quadlets `oep.env` (see the guide's Install page for
the full reference): `POSTGRES_USER/PASSWORD`,
`OEP_DJANGO_USER/OEP_DB_PW/OEP_DJANGO_HOST/NAME`,
`LOCAL_DB_USER/PASSWORD/NAME/HOST`, `FUSEKI_ADMIN_PASSWORD`, `FUSEKI_DATASET_1`,
`ONTOP_DB_URL/USER/PASSWORD`. Optional port overrides: `OEP_PORT_WEB` (8080),
`OEP_PORT_POSTGRES` (5432), `OEP_PORT_FUSEKI` (3030), `OEP_PORT_ONTOP` (8081),
`OEP_PORT_LOOKUP` (3004).

### Ubuntu 22.04 platform notes (Podman 3.x + compose)

These only apply to the **older Podman 3.x + podman-compose** combination.
Podman 4.x (netavark) and the Quadlets path are unaffected.

- **CNI plugin version mismatch** — Ubuntu 22.04 ships
  `containernetworking-plugins 0.9.1` (CNI spec 0.4.0) while Podman 3.x writes
  `cniVersion: 1.0.0`, breaking inter-container DNS. Fix: install newer CNI
  plugins into `~/.config/cni/plugins` (from the
  [containernetworking/plugins releases](https://github.com/containernetworking/plugins/releases))
  and point Podman at them via `cni_plugin_dirs` in
  `~/.config/containers/containers.conf`.
- **`--network` not passed by podman-compose** — `podman-compose` 1.5.0 with
  Podman 3.4.x ignores the `networks:` assignment, dropping containers on the
  DNS-less default network. Fix: `podman network create oep` and set
  `default_network = "oep"` in `~/.config/containers/containers.conf`.

## Reset the database (compose)

```sh
podman-compose --env-file podman/.env -f podman/podman-compose.yaml down
podman volume rm podman_pgdata   # check the exact name with: podman volume ls
podman-compose --env-file podman/.env -f podman/podman-compose.yaml up -d
```

The postgres container recreates all tables on a fresh volume automatically.

## Process count and database connections

`podman/apache2.conf` runs two mod_wsgi daemon groups, and both numbers in it
are coupled to something outside the file.

**Every process carries its own connection pool.** The pool's ceiling is per
process (`OEDB_POOL_SIZE + OEDB_MAX_OVERFLOW` in `oedb/connection.py`); the
database's is per cluster. So this has to hold:

```
total processes x (OEDB_POOL_SIZE + OEDB_MAX_OVERFLOW)  <  usable slots
```

where _usable slots_ is `max_connections` minus `superuser_reserved_connections`
on the OEDB. As shipped: `(4 + 1) x (2 + 15) = 85` against 247 measured on the
production database.

`api/tests/test_podman_apache_config.py` asserts it, so **raising a process
count fails the test suite until the pool is re-sized with it**. That is the
point. In September 2026 production raised a process count 4 -> 12 in an Apache
config no repository contained, nothing recomputed the pool, and the database
ran out of connection slots for twelve days ([#2495]).

**`/api/v0/advanced` runs on its own single-process group and must keep doing
so.** `api/sessions.py` keeps live database connections in a module-global dict
keyed by a `connection_id` handed back to the client, and mod_wsgi has no
session affinity. With more than one process a client that opens a connection
and then uses it lands on a different interpreter, misses the dict, and silently
gets a new connection -- or `Cursor not found`. The test checks this too.

**Choosing the process count.** The shipped 4 is not a measurement; production
runs 12, on a host with 32 cores whose thirteen daemons hold ~34 GiB resident.
Size it against the host this stack runs on, then re-run the test.

[#2495]: https://github.com/OpenEnergyPlatform/oeplatform/issues/2495

## Deploy a new release

For the production Quadlets path, follow the guide's
[Update page](../docs/installation/production-podman/update.md). For the compose
path, rebuild/pull the images and re-run `up -d`; release steps (migrations,
static files) run inside the container on start.
