<!--
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Update

!!! info "You are here"

    Step 4 of the **Production deployment (Podman)** guide, after
    **[Ontop](ontop.md)**. This page deploys a new release. Next: day-to-day
    **Maintenance & troubleshooting**.

## Today: build the images locally

The OEP-specific images (**application** and **ontop**) are **not published to a
registry yet**, so updating means rebuilding them on the host from the
checked-out source. The `postgres`, `fuseki` and `lookup` images are pulled and
rarely change.

```sh
# 1. Get the release you want to deploy
git fetch --all --tags
git checkout <tag-or-branch>
git pull

# 2. Keep the running image under a second name, to roll back to
podman tag ghcr.io/openenergyplatform/oeplatform-production:latest \
  ghcr.io/openenergyplatform/oeplatform-production:previous

#    Rebuild the application image (runs collectstatic + asset compression)
#    Build under the ghcr name the unit references (see Install) — no re-tag needed.
podman build -t ghcr.io/openenergyplatform/oeplatform-production:latest -f podman/Dockerfile .

# 3. Rebuild ontop only if its ontology/mapping/driver changed
podman build -t ghcr.io/openenergyplatform/oeplatform-ontop:latest -f docker/Dockerfile.ontop docker/

# 4. Restart the app (postgres and fuseki keep running)
systemctl --user restart oep-oeplatform
# restart ontop too if you rebuilt it:
systemctl --user restart oep-ontop
```

### What happens on restart

Release steps run **inside the container** automatically on start — you do
**not** run them by hand:

| Manual (legacy bare-metal) step   | Where it runs now                    |
| --------------------------------- | ------------------------------------ |
| `npm ci` / `npm run build`        | in the image build (Dockerfile)      |
| `pip install -r requirements.txt` | in the image build (Dockerfile)      |
| `collectstatic` / `compress`      | in the image build (Dockerfile)      |
| `manage.py migrate`               | on container start (`entrypoint.sh`) |
| `alembic upgrade head`            | on container start (`entrypoint.sh`) |
| `touch wsgi.py` / reload Apache   | container restart                    |

!!! warning "Database migrations run automatically"

    Django + Alembic migrations execute on app-container start. Before deploying a
    release that includes migrations, make sure you have a **current database
    backup** (see **[Maintenance](maintenance.md)**).

### Roll back

If the new image does not come up, put the previous one back under the name the
unit starts and restart:

```sh
podman tag ghcr.io/openenergyplatform/oeplatform-production:previous \
  ghcr.io/openenergyplatform/oeplatform-production:latest
systemctl --user restart oep-oeplatform
```

This returns the code only. Migrations the new image already applied stay in the
database; undoing them needs the backup taken before the update.

## Once: move Fuseki's data into its volume

Earlier versions of `oep-fuseki.container` mounted the `fuseki-databases` volume
at `/home/fuseki/databases`, a path Fuseki never uses. The image keeps
everything under `/fuseki` (datasets, dataset registry, `shiro.ini`), which was
therefore an anonymous volume, and the unit removes that with the container.
**Any restart of `oep-fuseki`, or a reboot, deleted the OEKG.** The unit now
mounts the volume at `/fuseki`.

!!! danger "Copy before you restart"

    On a host installed with the old unit, the OEKG exists only in the running
    container. Re-running `install.sh` changes nothing yet, but the next
    restart of `oep-fuseki` starts from an empty store. Do the copy below first.

```sh
# 1. Count the triples, to compare afterwards
curl -s http://localhost:3030/ds/query -H 'Accept: text/csv' \
  --data-urlencode 'query=SELECT (COUNT(*) AS ?n) {{?s ?p ?o} UNION {GRAPH ?g {?s ?p ?o}}}'

# 2. Stop the app, the only writer, so the copy is consistent
systemctl --user stop oep-oeplatform

# 3. Copy /fuseki from the running container into the named volume.
#    No --rm: it would try to remove the volumes taken over from `fuseki`.
podman run --name fuseki-copy --user root --volumes-from fuseki \
  -v systemd-fuseki-databases:/new --entrypoint sh \
  docker.io/stain/jena-fuseki:5.1.0 \
  -c 'cp -a /fuseki/. /new/ && find /new -name tdb.lock -delete'
podman rm fuseki-copy

# 4. Install the new unit and restart onto the volume
bash podman/quadlets/install.sh
systemctl --user restart oep-fuseki
systemctl --user start oep-oeplatform
```

Then repeat the count from step 1: it must be the same, and
`journalctl --user -u oep-fuseki` must not show
`Initializing Apache Jena Fuseki` for this start.
`podman inspect fuseki --format '{{range .Mounts}}{{.Name}} {{end}}'` lists only
`systemd-fuseki-databases`.

!!! note "The admin password lives in the volume"

    The image writes `ADMIN_PASSWORD` into `/fuseki/shiro.ini` on the first
    start only. With `/fuseki` kept, a later change of the variable has no
    effect; change `shiro.ini` in the volume instead.

## Forthcoming: pull published images

Once a tagged release (`v*`) publishes the application and ontop images to the
registry, the update flow becomes a **pull** instead of a local build. The
published image is self-contained, so **you do not need the application source
(no `git pull`) just to get a new image**:

```sh
# (forthcoming — not yet available)
podman pull ghcr.io/openenergyplatform/oeplatform-production:latest
podman pull ghcr.io/openenergyplatform/oeplatform-ontop:latest
systemctl --user restart oep-oeplatform oep-ontop
```

!!! info "When do you still need `git pull`?"

    Only when the **deployment config** in the repo changed — the quadlet unit
    files, `install.sh`, `oep.env.example`, or the nginx / lookup service configs.
    Those live in the repo, **not** in the image. If a release touches them,
    `git pull` and re-run `bash podman/quadlets/install.sh` (and
    `install-nginx.sh` if the nginx config changed) before restarting. If only the
    application changed, the two `podman pull`s above are enough.

!!! note "Not enabled yet"

    Until image publishing lands, use the **local build** flow above — which
    **does** require `git pull`, because there the image is built from the
    checkout. The image names shown here are the intended published names; building
    locally under the same names keeps the switch seamless later.

---

**Next → [Maintenance & troubleshooting](maintenance.md)** — logs, restarts,
resets, and common failure modes.
