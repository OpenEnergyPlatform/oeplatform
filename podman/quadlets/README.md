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

## Serving over HTTPS with nginx (TLS terminated upstream)

The `oep-oeplatform.container` publishes the app on **`127.0.0.1:8080`** only —
it is not reachable from outside the server. An nginx reverse proxy on the host
listens on **port 443** and forwards to the container.

> **Where is TLS?** HTTPS is terminated by an **upstream proxy / load balancer**
> in front of this host. It forwards already-decrypted **plain HTTP to this host
> on port 443** (the only port open to the LB) — so nginx here listens on 443
> _without_ `ssl` and holds no certificates. nginx runs as root, so it can bind
> the privileged port 443 even though the app container is rootless. It exists
> to (a) bind 443 in front of the rootless container, (b) keep that container
> bound to localhost, and (c) forward the original request headers (notably
> `X-Forwarded-Proto`) so Django knows the client used HTTPS.

### 1. Tell Django it runs behind HTTPS

In `~/.config/oeplatform/oep.env` set the production block (see
`oep.env.example`):

```sh
OEP_DEBUG=False
OEP_URL=your-domain.org
OEP_ALLOWED_HOSTS=your-domain.org
OEP_BEHIND_TLS_PROXY=True
OEP_CSRF_TRUSTED_ORIGINS=https://your-domain.org
```

`OEP_BEHIND_TLS_PROXY=True` makes Django trust the `X-Forwarded-Proto` header
that the upstream sets and this nginx forwards. Restart the app so it picks up
the new environment file:

```sh
systemctl --user restart oep-oeplatform
```

### 2. Install and configure nginx

```sh
bash podman/nginx/install-nginx.sh
```

This installs nginx (if needed), writes the site config with the `server_name`
taken from `OEP_URL` in your `oep.env`, enables it, disables the default site,
and reloads nginx. It is idempotent — re-run it after changing the config or
domain. To override the domain, pass it explicitly:
`bash podman/nginx/install-nginx.sh my-domain.org`.

> The config listens on `443` (plain HTTP — TLS is terminated upstream). If your
> upstream forwards to a different port, adjust the `listen` directive in
> `podman/nginx/oeplatform.conf` and re-run the script.

The platform is now served over HTTPS via the upstream proxy. No certificates
are configured on this host.

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

## Repo Path for Lookup

`oep-lookup.container` bind-mounts its config from this repository. The unit
ships with an `@@OEP_REPO@@` placeholder that `install.sh` replaces with the
absolute path of your checkout when it installs the units — so it works from any
location with **no symlink and no manual editing**. Just run `install.sh` from
the checkout you want to use.

> `oep-ontop.container` needs no repo path at all — its ontology, mapping and
> JDBC driver are baked into the image and its DB connection comes from
> `oep.env` (`ONTOP_DB_URL` / `ONTOP_DB_USER` / `ONTOP_DB_PASSWORD`).

## Uninstall

```sh
systemctl --user disable --now \
  oep-postgres oep-fuseki oep-oeplatform oep-ontop oep-lookup

rm ~/.config/containers/systemd/oep-*.container
rm ~/.config/containers/systemd/*.volume
rm ~/.config/containers/systemd/oep.network

systemctl --user daemon-reload
```
