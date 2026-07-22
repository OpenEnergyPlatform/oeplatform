<!--
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Install

!!! info "You are here"

    Step 2 of the **Production deployment (Podman)** guide. Read
    **[Overview & architecture](index.md)** first if you haven't. This page brings
    the full stack up on a fresh host. Next you'll configure **Ontop**.

Run all commands from the **repository root**, as the **unprivileged service
user** that owns the containers (not root). The nginx step near the end is the
only part that needs root.

## Prerequisites

- **Podman ≥ 4.4** with rootless configured — your user needs entries in
  `/etc/subuid` and `/etc/subgid`.
- **systemd** available for the user session (`systemctl --user`).
- A user checkout of the `oeplatform` repository.
- Outbound network access for the first image build (downloads the OEO release,
  the JDBC driver, and base images).

!!! note "Podman 4.x assumed"

    This guide targets Podman 4.x (netavark backend, native DNS). Quadlets attach
    each container to the `oep` network explicitly, so the older podman-compose
    networking workarounds do not apply here.

## 1. Install the units and create the environment file

```sh
bash podman/quadlets/install.sh
```

This copies the Quadlet unit files (`*.container`, `*.volume`, `oep.network`)
into `~/.config/containers/systemd/`, creates `~/.config/oeplatform/oep.env`
from the example template, and substitutes the absolute path of your checkout
into the units that need it (so there are **no symlinks and no manual path
edits**).

## 2. Fill in the environment file

```sh
$EDITOR ~/.config/oeplatform/oep.env
```

For a first bring-up you only need the database and Fuseki credentials; the
HTTPS block comes later in this page.

| Variable                                               | Description                                                   |
| ------------------------------------------------------ | ------------------------------------------------------------- |
| `POSTGRES_USER` / `POSTGRES_PASSWORD`                  | PostgreSQL superuser credentials.                             |
| `OEP_DJANGO_USER` / `OEP_DB_PW`                        | DB user Django connects as (often the same as the superuser). |
| `OEP_DJANGO_HOST` / `OEP_DJANGO_NAME`                  | Keep as `postgres` / `oep_django`.                            |
| `LOCAL_DB_USER` / `LOCAL_DB_PASSWORD`                  | Credentials for the OEDB (`oedb`) database.                   |
| `LOCAL_DB_HOST` / `LOCAL_DB_NAME`                      | Keep as `postgres` / `oedb`.                                  |
| `FUSEKI_ADMIN_PASSWORD`                                | Fuseki web UI admin password.                                 |
| `FUSEKI_DATASET_1`                                     | Fuseki dataset name — keep as `ds`.                           |
| `ONTOP_DB_URL` / `ONTOP_DB_USER` / `ONTOP_DB_PASSWORD` | Ontop's connection to the OEDB — see **Ontop**.               |

!!! warning "The CSRF origin needs a scheme"

    `OEP_CSRF_TRUSTED_ORIGINS` must include the URL scheme
    (`https://your-domain.org`, not `your-domain.org`). A scheme-less value makes
    Django reject the config at startup.

## 3. Obtain the images

Two images are OEP-specific: the **application** image and the **ontop** image.
Today they are built locally (image publishing is forthcoming — see
**[Update](update.md)**). The `postgres`, `fuseki` and `lookup` images are
pulled automatically.

```sh
podman build -t localhost/oeplatform:latest -f podman/Dockerfile .
podman build -t localhost/oep-ontop:latest -f docker/Dockerfile.ontop docker/
```

!!! note "The build is slow the first time"

    The application build runs `collectstatic` + asset compression, which
    dominates build time. This is expected. The image bakes in the ontology so
    Django can start.

## 4. Configure the lookup service

The lookup service is driven by config that lives in the repository and is
mounted into the container (the install script resolves the path for you — no
manual editing).

- **`podman/serviceConfigs/lookup/config.yaml`** — the service config. It
  defines the searchable `lookupFields` (`id`, `label`, `definition`) and match
  tuning (`exactMatchBoost`, `prefixMatchBoost`, `fuzzyMatchBoost`,
  `fuzzyEditDistance`, `maxResults`, `minScore`). Adjust these to change
  ranking/behaviour.
- **Indexers** — each indexer declares `indexMode: INDEX_SPARQL_ENDPOINT`, a
  `sparqlEndpoint`, and `indexFields` (one SPARQL query per field). The
  reference indexer indexes OWL classes with three fields:

  | Field        | Populated from                            |
  | ------------ | ----------------------------------------- |
  | `label`      | `rdfs:label` (English)                    |
  | `type`       | a bound literal `"class"` per `owl:Class` |
  | `definition` | `obo:IAO_0000115` (English)               |

  To index a different source or expose different fields, add or edit an indexer
  entry and restart the lookup service.

!!! warning "Indexer wiring is still being finished for this path"

    The indexer config and its Fuseki endpoint currently ship with the
    **development** setup; wiring the ontology into Fuseki and shipping the indexer
    for the production Podman path is in progress. Until it lands, the lookup
    service starts but has no populated index behind it on this path. The structure
    above is what it indexes once wired.

## 5. Enable and start the services

```sh
systemctl --user enable --now \
  oep-postgres oep-fuseki oep-oeplatform oep-ontop oep-lookup
```

Services start in dependency order — `oep-oeplatform` and `oep-ontop` wait for
`oep-postgres`. Database migrations and static-file steps run automatically
inside the app container on start. Check status and logs:

```sh
systemctl --user status oep-oeplatform
journalctl --user -u oep-oeplatform -f
```

At this point the app is listening on `127.0.0.1:8080` only. It is **not** yet
reachable from outside the host.

## 6. Serve over HTTPS with nginx

nginx (root) terminates TLS on `:443` and proxies to the container on
`127.0.0.1:8080`.

### 6a. Tell Django it runs behind HTTPS

In `~/.config/oeplatform/oep.env`, set the production block:

```sh
OEP_DEBUG=False
OEP_URL=your-domain.org
OEP_ALLOWED_HOSTS=your-domain.org
OEP_BEHIND_TLS_PROXY=True
OEP_CSRF_TRUSTED_ORIGINS=https://your-domain.org
```

`OEP_BEHIND_TLS_PROXY=True` makes Django trust the `X-Forwarded-Proto` header
the proxy chain sets, so it treats the request as HTTPS (secure cookies, correct
redirects). Restart the app so it picks up the change:

```sh
systemctl --user restart oep-oeplatform
```

### 6b. Install and configure nginx (needs root)

```sh
sudo bash podman/nginx/install-nginx.sh
```

This installs nginx (if needed), **generates a self-signed backend TLS
certificate** (if none exists under `/etc/nginx/ssl/oeplatform/`), writes the
site config with `server_name` taken from `OEP_URL` in `oep.env`, enables the
site, disables the default site, and reloads nginx. It is **idempotent** —
re-run it after changing the domain or config. To override the domain:
`sudo bash podman/nginx/install-nginx.sh your-domain.org`.

!!! note "Which certificate?"

    Behind an upstream proxy that re-encrypts to this host, a **self-signed**
    backend cert is fine (the proxy typically does not verify it). To use a real
    certificate instead, drop `fullchain.pem` + `privkey.pem` into
    `/etc/nginx/ssl/oeplatform/` **before** running the script.

!!! tip "Two-user servers"

    If containers run under one user and you `sudo` as another, run the container
    steps (1–5) as the service user and only this nginx step via `sudo`. The script
    handles being run as root.

## 7. Make services survive logout and reboot

Rootless `--user` services stop when the user logs out unless **linger** is
enabled:

```sh
sudo loginctl enable-linger <service-user>
```

With linger on, systemd keeps the user's services running across logout and
starts the enabled ones on boot.

## Verify

- `systemctl --user status 'oep-*'` — all units `active (running)`.
- `curl -kI https://your-domain.org` (or the host directly) returns `200`/`302`.
- The platform loads in a browser at `https://your-domain.org`.

---

**Next → [Ontop](ontop.md)** — the SPARQL-over-SQL service and how to apply a
real mapping.
