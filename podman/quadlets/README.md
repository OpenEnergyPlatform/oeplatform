<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Quadlets — Podman Systemd Integration

> Alternative to `podman-compose`. Each service is a systemd unit managed
> directly by `systemctl`. Requires Podman ≥ 4.4 and a rootless Podman setup.

Quadlets translate `.container`, `.volume`, and `.network` files into systemd
units. systemd then manages the full lifecycle: start on boot, restart on
failure, dependency ordering, and log access via `journalctl`.

## Files

| File                           | Type      | Description                                |
| ------------------------------ | --------- | ------------------------------------------ |
| `oep.network`                  | network   | Shared network for all services            |
| `pgdata.volume`                | volume    | PostgreSQL data                            |
| `fuseki-databases.volume`      | volume    | Fuseki triple store data                   |
| `oeplatform-ontologies.volume` | volume    | OEO ontologies (downloaded at first start) |
| `oeplatform-media.volume`      | volume    | Media files and OEO-extended               |
| `oep-postgres.container`       | container | PostgreSQL database                        |
| `oep-fuseki.container`         | container | Apache Jena Fuseki                         |
| `oep-oeplatform.container`     | container | OEP web app (Apache2)                      |
| `oep-ontop.container`          | container | Ontop SPARQL endpoint                      |
| `oep-lookup.container`         | container | DBpedia Lookup service                     |

The `Dockerfile`, `apache2.conf`, and `entrypoint.sh` in the parent `podman/`
directory are shared with the podman-compose setup — both approaches build and
run the same image.

## First-time Setup

Run all commands from the **repository root**.

### 1. Install units and create the environment file

```sh
bash podman/quadlets/install.sh
```

This copies all unit files to `~/.config/containers/systemd/` and creates
`~/.config/oeplatform/oep.env` from the example template.

### 2. Fill in credentials

```sh
$EDITOR ~/.config/oeplatform/oep.env
```

### 3. Build the application images

```sh
podman build -t localhost/oeplatform:latest -f podman/Dockerfile .
podman build -t localhost/oep-ontop:latest -f docker/Dockerfile.ontop docker/
```

### 4. Enable and start all services

```sh
systemctl --user enable --now \
  oep-postgres oep-fuseki oep-oeplatform oep-ontop oep-lookup
```

Services start in dependency order. `oep-oeplatform` and `oep-ontop` wait for
`oep-postgres` before starting.

## Managing Services

```sh
# Status
systemctl --user status oep-oeplatform

# Logs
journalctl --user -u oep-oeplatform -f

# Restart a single service
systemctl --user restart oep-oeplatform

# Stop everything
systemctl --user stop oep-postgres oep-fuseki oep-oeplatform oep-ontop oep-lookup
```

## Deploy a New Release

```sh
git checkout master && git pull

# Rebuild the application image
podman build -t localhost/oeplatform:latest -f podman/Dockerfile .

# Restart the app container — postgres and fuseki keep running
systemctl --user restart oep-oeplatform
```

## Repo Path for Ontop and Lookup

The `oep-ontop.container` and `oep-lookup.container` files bind-mount config
files from the repository. They default to `/opt/oeplatform`. If your checkout
is elsewhere, update the `Volume=` lines in both files, or create a symlink:

```sh
sudo ln -s /your/actual/repo/path /opt/oeplatform
```

## Uninstall

```sh
systemctl --user disable --now \
  oep-postgres oep-fuseki oep-oeplatform oep-ontop oep-lookup

rm ~/.config/containers/systemd/oep-*.container
rm ~/.config/containers/systemd/*.volume
rm ~/.config/containers/systemd/oep.network

systemctl --user daemon-reload
```
