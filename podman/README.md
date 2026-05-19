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

## First-time Setup

### 1. Create your environment file

```sh
cp podman/.env.example .env
# edit .env and fill in all values — this file must never be committed
```

`podman-compose` automatically loads `.env` from the repository root when run
from there. The `.gitignore` already excludes `.env` files.

### 2. Build the images

```sh
podman-compose -f podman/podman-compose.yaml build
```

The build runs the Vite frontend build and the Django `collectstatic` /
`compress` steps inside the container — no local Node.js or Python needed.

### 3. Start the stack

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

## Deploy a New Release

Checkout the release branch/tag, rebuild the image, and restart the stack. All
release steps run automatically — no manual server commands needed.

```sh
git checkout master   # or the release tag, e.g. git checkout v1.8.0
git pull

podman-compose -f podman/podman-compose.yaml build
podman-compose -f podman/podman-compose.yaml up -d
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
