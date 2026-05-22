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

- [Podman](https://podman.io/getting-started/installation) ≥ 3.4
- [podman-compose](https://github.com/containers/podman-compose) ≥ 1.0
- Rootless Podman configured (`/etc/subuid` and `/etc/subgid` entries for your
  user)
- `dnsmasq` installed (required by the CNI dnsname plugin for inter-container
  DNS resolution)

Install podman-compose via pip (the apt package on Ubuntu 22.04 is too old):

```sh
pip install podman-compose
```

## Platform Notes

### Ubuntu 22.04 — CNI plugin version mismatch

Ubuntu 22.04 ships `containernetworking-plugins 0.9.1`, which only supports CNI
spec `0.4.0`. Podman 3.x creates new networks with `cniVersion: 1.0.0`, causing
the `firewall` CNI plugin to reject the config and silently break
inter-container networking. Fix it by installing updated plugin binaries into a
user directory and pointing Podman at them:

```sh
# Download CNI plugins v1.9.1 (or later)
curl -LO https://github.com/containernetworking/plugins/releases/download/v1.9.1/cni-plugins-linux-amd64-v1.9.1.tgz
mkdir -p ~/.config/cni/plugins
tar -xzf cni-plugins-linux-amd64-v1.9.1.tgz -C ~/.config/cni/plugins
rm cni-plugins-linux-amd64-v1.9.1.tgz

# Tell Podman to search the user directory first
mkdir -p ~/.config/containers
cat >> ~/.config/containers/containers.conf << 'EOF'
[network]
cni_plugin_dirs = ["/home/<your-user>/.config/cni/plugins", "/usr/lib/cni", "/opt/cni/bin"]
EOF
```

Replace `<your-user>` with your actual username or use `$HOME`.

### Ubuntu 22.04 — podman-compose does not pass `--network` to podman run

`podman-compose` 1.5.0 with Podman 3.4.x has a bug where the `networks:` service
assignment is ignored and all containers land on the default `podman` network,
which has no DNS. The workaround is to pre-create the `oep` network and make it
the default:

```sh
podman network create oep

cat >> ~/.config/containers/containers.conf << 'EOF'
default_network = "oep"
EOF
```

This makes the `oep` network — which has the dnsname plugin — the network all
containers use unless explicitly overridden.

> **Note:** This issue does not affect Podman 4.x (Netavark backend, native DNS)
> or the Quadlets deployment path (see below), which attach containers to the
> network via explicit `Network=oep.network` directives in the unit files.

## First-time Setup

### 1. Create your environment file

```sh
cp podman/.env.example podman/.env
```

Edit `podman/.env` and fill in all values. The file is read by `podman-compose`
at startup and must never be committed (it is gitignored).

| Variable                | Description                                                          |
| ----------------------- | -------------------------------------------------------------------- |
| `POSTGRES_USER`         | PostgreSQL superuser name                                            |
| `POSTGRES_PASSWORD`     | PostgreSQL superuser password                                        |
| `OEP_DJANGO_USER`       | DB user Django connects as (usually same as `POSTGRES_USER`)         |
| `OEP_DB_PW`             | Password for `OEP_DJANGO_USER`                                       |
| `OEP_DJANGO_HOST`       | Hostname of the postgres container — keep as `postgres`              |
| `OEP_DJANGO_NAME`       | Django database name — keep as `oep_django`                          |
| `LOCAL_DB_USER`         | User for the local (oedb) database — usually same as `POSTGRES_USER` |
| `LOCAL_DB_PASSWORD`     | Password for `LOCAL_DB_USER`                                         |
| `LOCAL_DB_NAME`         | Local database name — keep as `oedb`                                 |
| `LOCAL_DB_HOST`         | Hostname of the postgres container — keep as `postgres`              |
| `FUSEKI_ADMIN_PASSWORD` | Fuseki web UI admin password                                         |
| `FUSEKI_DATASET_1`      | Fuseki dataset name — keep as `ds`                                   |

Optional port overrides (defaults shown):

```sh
OEP_PORT_WEB=8080
OEP_PORT_POSTGRES=5432
OEP_PORT_FUSEKI=3030
OEP_PORT_ONTOP=8081
OEP_PORT_LOOKUP=3004
```

### 2. Start the stack

See [Start the Stack](#start-the-stack) below.

---

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
podman-compose --env-file podman/.env -f podman/podman-compose.yaml up -d
```

## Stop the Stack

```sh
podman-compose --env-file podman/.env -f podman/podman-compose.yaml down
```

## Override Ports

Default ports can be changed via environment variables before starting:

```sh
export OEP_PORT_WEB=9090
export OEP_PORT_POSTGRES=5433
```

## View Logs

```sh
podman-compose --env-file podman/.env -f podman/podman-compose.yaml logs -f oeplatform
# or directly:
podman logs -f oeplatform
```

## Open a Shell

```sh
podman exec -it oeplatform bash
```

## Reset Database

```sh
podman-compose --env-file podman/.env -f podman/podman-compose.yaml down
podman volume rm podman_pgdata   # check exact name with: podman volume ls
podman-compose --env-file podman/.env -f podman/podman-compose.yaml up -d
```

The postgres container recreates all tables on a fresh volume automatically.

## Deploy a New Release

Pull the latest production images and restart — all release steps run inside the
container automatically (migrations, static files, etc.).

```sh
git pull
podman pull ghcr.io/openenergyplatform/oeplatform-production:latest
podman pull ghcr.io/openenergyplatform/oeplatform-ontop:latest
podman-compose --env-file podman/.env -f podman/podman-compose.yaml up -d
```

## Quadlets (systemd) Alternative

The `quadlets/` directory contains systemd Quadlet unit files as an alternative
to podman-compose. Quadlets are better suited for long-running production
servers because systemd manages restarts, dependencies, and logging.

**Why Quadlets are simpler on Podman 3.x:** Each `.container` file declares
`Network=oep.network` explicitly. Systemd creates the network via the
`oep.network` unit and attaches every container before it starts. This bypasses
the podman-compose network assignment bug entirely — no `default_network`
workaround needed.

You still need the CNI plugin fix from the
[Ubuntu 22.04 section](#ubuntu-2204--cni-plugin-version-mismatch) if running on
Ubuntu 22.04.

```sh
bash podman/quadlets/install.sh
systemctl --user enable --now oep-postgres oep-fuseki oep-oeplatform oep-ontop oep-lookup
```

View logs via journald:

```sh
journalctl --user -u oep-oeplatform -f
```

### What runs where

The table below maps the manual server release steps to their Podman equivalent.

| Manual step (ovgu-toep-w)                     | Podman equivalent                           |
| --------------------------------------------- | ------------------------------------------- |
| `git checkout master && git pull`             | `git checkout <tag> && git pull` on host    |
| `npm install --no-save`                       | `npm ci` in Dockerfile (image build)        |
| `npm run build`                               | `npm run build` in Dockerfile (image build) |
| `pip install -r requirements.txt`             | `pip install` in Dockerfile (image build)   |
| `python manage.py collectstatic --noinput`    | Dockerfile build step                       |
| `python manage.py compress`                   | `compress --force` in Dockerfile build step |
| `python manage.py migrate`                    | `entrypoint.sh` on container start          |
| `python manage.py alembic upgrade head`       | `entrypoint.sh` on container start          |
| `touch wsgi.py` / `systemctl reload apache24` | `podman-compose up -d` restarts container   |
