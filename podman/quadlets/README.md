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

### 1. Install nginx and the site config

```sh
sudo apt install nginx
sudo cp podman/nginx/oeplatform.conf /etc/nginx/sites-available/oeplatform
sudo ln -s /etc/nginx/sites-available/oeplatform /etc/nginx/sites-enabled/oeplatform
sudo rm -f /etc/nginx/sites-enabled/default
```

Edit `/etc/nginx/sites-available/oeplatform`:

- Replace `openenergyplatform.example.org` with your real domain.
- The config listens on `443` (plain HTTP — TLS is terminated upstream). If your
  upstream forwards to a different port, adjust the `listen` directive to match.

### 2. Tell Django it runs behind HTTPS

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
that the upstream sets and this nginx forwards. Then restart the app so it picks
up the new environment file:

```sh
systemctl --user restart oep-oeplatform
```

### 3. Enable nginx

```sh
sudo nginx -t && sudo systemctl reload nginx
```

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
