<!--
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Maintenance & troubleshooting

!!! info "You are here"

    Final page of the **Production deployment (Podman)** guide, after
    **[Update](update.md)**. Day-to-day operations plus the failure modes seen
    during bring-up.

## Everyday operations

```sh
# Status of one service / all services
systemctl --user status oep-oeplatform
systemctl --user status 'oep-*'

# Follow logs
journalctl --user -u oep-oeplatform -f

# Restart one service (dependencies keep running)
systemctl --user restart oep-oeplatform

# Stop / start everything
systemctl --user stop  oep-postgres oep-fuseki oep-oeplatform oep-ontop oep-lookup
systemctl --user start oep-postgres oep-fuseki oep-oeplatform oep-ontop oep-lookup
```

Open a shell in the app container:

```sh
podman exec -it oeplatform bash
```

!!! tip "Ontop operations live on their own page"

    For applying/updating the ontop mapping, rebuilding with a different JDBC
    version, or the lazy-init behaviour, see **[Ontop](ontop.md)** — that procedure
    is not repeated here.

## Backups

Persistent state is in named volumes (physically under the service user's home).
At minimum, back up the **Postgres** data and the **media** volume regularly,
and always before a release that runs migrations. List volumes and their
locations:

```sh
podman volume ls
podman volume inspect pgdata
```

Use `pg_dump` from inside/against the postgres container for logical database
backups, and snapshot the media volume for uploaded files. (Physical volume
placement per server is a separate storage-configuration concern, out of scope
for this generic guide.)

## Reset the database (destructive)

This **deletes all database data**. Only for a throwaway/dev-like environment.

```sh
systemctl --user stop oep-oeplatform oep-postgres
podman volume rm pgdata        # confirm the exact name with: podman volume ls
systemctl --user start oep-postgres oep-oeplatform
```

The postgres container recreates the schema on a fresh volume; the app re-runs
migrations on start.

## Troubleshooting — common failure modes

These are the issues most likely to bite during a first deployment.

### CSRF "origin not trusted" / config error at startup

**Symptom:** Django rejects form posts, or refuses to start complaining about
`CSRF_TRUSTED_ORIGINS`.

**Cause:** `OEP_CSRF_TRUSTED_ORIGINS` values must include a **scheme**.

**Fix:** use `https://your-domain.org`, not `your-domain.org`. Multiple origins
are comma-separated. Restart the app after editing `oep.env`.

### `DisallowedHost` / blank page after DNS resolves

**Symptom:** `Invalid HTTP_HOST header` in the logs, or the site 400s.

**Cause:** the request's host isn't in `OEP_ALLOWED_HOSTS`.

**Fix:** set `OEP_ALLOWED_HOSTS` to the exact public domain (comma-separated if
several), then `systemctl --user restart oep-oeplatform`.

### App can't reach the database / `could not translate host name "postgres"`

**Symptom:** the app or ontop logs a DNS failure for `postgres`.

**Cause:** the postgres container isn't running, or the service isn't on the
`oep` network.

**Fix:** `systemctl --user status oep-postgres` — start it if it's down. All
services must be on the `oep` network (Quadlets attach them automatically);
confirm with `podman network inspect oep`.

### Postgres won't start / `POSTGRES_PASSWORD not specified`

**Symptom:** the postgres container exits immediately on first start.

**Cause:** empty or mistyped DB credentials in `oep.env`.

**Fix:** fill in `POSTGRES_USER` / `POSTGRES_PASSWORD` (and the `LOCAL_DB_*`
values) — watch for typos. Restart the service.

### Service fails with exit code 125

**Symptom:** `systemctl --user status` shows the unit failed with status 125.

**Cause:** Podman couldn't find the image under the name the unit expects
(image-name mismatch) — common when you built an image under one tag but the
unit references another.

**Fix:** confirm the image exists under the exact name the unit uses
(`podman images`), and re-tag if needed, e.g.
`podman tag localhost/oeplatform:latest <expected-name>`.

### Lookup service fails to start / can't find its config

**Symptom:** the lookup unit fails, complaining about a missing config path.

**Cause:** the config bind-mount path didn't resolve to your checkout.

**Fix:** the install script substitutes the checkout path into the unit for you
— re-run `bash podman/quadlets/install.sh` from the checkout you want to use,
then `systemctl --user daemon-reload` and restart the service. (Do not add
symlinks — the path is resolved automatically.)

### Upstream proxy shows "Error during SSL Handshake with remote server"

**Symptom:** the browser gets a proxy error; the upstream proxy log mentions a
backend SSL handshake failure.

**Cause:** the upstream proxy re-encrypts to this host over **HTTPS**, but nginx
here isn't terminating TLS (e.g. it's listening plain HTTP, or has no
certificate).

**Fix:** ensure nginx listens `443 ssl` with a certificate present under
`/etc/nginx/ssl/oeplatform/`. Re-run `sudo bash podman/nginx/install-nginx.sh`
to regenerate the self-signed cert and site config, then reload nginx.

### Services vanish after logout / don't come back after reboot

**Symptom:** everything stops when you log out, or nothing runs after a reboot.

**Cause:** linger isn't enabled for the service user.

**Fix:** `sudo loginctl enable-linger <service-user>`, and make sure the units
are `enable`d (`systemctl --user enable oep-*`).

## Where to look

| Symptom area     | First command                                           |
| ---------------- | ------------------------------------------------------- |
| App behaviour    | `journalctl --user -u oep-oeplatform -f`                |
| Database         | `journalctl --user -u oep-postgres -f`                  |
| SPARQL-over-SQL  | `journalctl --user -u oep-ontop -f` + [Ontop](ontop.md) |
| TLS / proxy      | nginx error log + `sudo nginx -t`                       |
| Networking / DNS | `podman network inspect oep`                            |

---

That's the full production deployment path: **[Overview](index.md) →
[Install](install.md) → [Ontop](ontop.md) → [Update](update.md) → Maintenance**.
For the OEP team's concrete server values, see the internal runbook (kept
outside this public documentation).
