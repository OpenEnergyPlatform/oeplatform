<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Quadlets — Podman Systemd Integration

> The **production** deployment path. Each service is a systemd `--user` unit
> generated from a `.container` / `.volume` / `.network` file. Requires rootless
> Podman ≥ 4.4.

**📖 Canonical guide:** the full install / update / maintenance documentation
lives in the project docs under **Production deployment (Podman)**
([`docs/installation/production-podman/`](../../docs/installation/production-podman/index.md)).
This README is only a quickstart — the guide is the source of truth.

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

## Quickstart

Run from the **repository root**, as the unprivileged service user:

```sh
# 1. Install units + create ~/.config/oeplatform/oep.env
bash podman/quadlets/install.sh

# 2. Fill in credentials + the HTTPS block
$EDITOR ~/.config/oeplatform/oep.env

# 3. Build the two OEP images UNDER THE GHCR NAMES the units reference
#    (pull policy 'missing' → a local image with that name is used as-is)
podman build -t ghcr.io/openenergyplatform/oeplatform-production:latest -f podman/Dockerfile .
podman build -t ghcr.io/openenergyplatform/oeplatform-ontop:latest    -f docker/Dockerfile.ontop docker/

# 4. Enable + start everything
systemctl --user enable --now oep-postgres oep-fuseki oep-oeplatform oep-ontop oep-lookup

# 5. HTTPS via nginx (needs root) + survive reboot
sudo bash podman/nginx/install-nginx.sh
sudo loginctl enable-linger <service-user>
```

See the [canonical guide](../../docs/installation/production-podman/index.md)
for the architecture, the `oep.env` reference, the Ontop mapping procedure, the
update flow, and troubleshooting.
