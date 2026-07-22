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

# 2. Rebuild the application image (runs collectstatic + asset compression)
podman build -t localhost/oeplatform:latest -f podman/Dockerfile .

# 3. Rebuild ontop only if its ontology/mapping/driver changed
podman build -t localhost/oep-ontop:latest -f docker/Dockerfile.ontop docker/

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

## Forthcoming: pull published images

Once a tagged release (`v*`) publishes the application and ontop images to the
registry, the update flow becomes a **pull** instead of a local build:

```sh
# (forthcoming — not yet available)
git pull
podman pull ghcr.io/openenergyplatform/oeplatform-production:latest
podman pull ghcr.io/openenergyplatform/oeplatform-ontop:latest
systemctl --user restart oep-oeplatform oep-ontop
```

!!! note "Not enabled yet"

    Until image publishing lands, use the **local build** flow above. The image
    names shown here are the intended published names; building locally under the
    same names keeps the switch seamless later.

---

**Next → [Maintenance & troubleshooting](maintenance.md)** — logs, restarts,
resets, and common failure modes.
