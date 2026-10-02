#!/usr/bin/env bash
set -euo pipefail

# give Postgres a moment
sleep 5

# ----------------------------------------------------------------
# Ownership of bind-mounted paths.
# We use the *numeric* uid:gid of the current process rather than the
# `appuser:appgroup` names: on macOS the host GID (e.g. 20) already exists in
# the base image, so no group literally named `appgroup` is created and
# `chown appuser:appgroup` fails with "invalid group".
OWNER="$(id -u):$(id -g)"

# own MODE PATH... - give PATH to the container user and set MODE on it.
# The container runs as a non-root user (compose's `user:`), so chown only
# succeeds where it is a no-op and chmod only on files we already own. Neither
# is fatal: files created on the host may refuse both, and the container can
# usually still read them. A path we could not fix is reported, then the boot
# goes on.
own() {
  local mode="$1"
  shift
  chown -R "$OWNER" "$@" 2>/dev/null || true
  chmod -R "$mode" "$@" 2>/dev/null \
    || echo "WARNING: could not set permissions on $*; continuing" >&2
}

# ----------------------------------------------------------------
# Bootstrap permissions on bind-mounted dirs so appuser can write
# ----------------------------------------------------------------
for d in ontologies media/oeo_ext static; do
  TARGET="/home/appuser/app/$d"

  # ensure the directory exists
  mkdir -p "$TARGET"

  # owner & group: read/write + conditional-exec (dirs executable,
  # files only if already marked) ; others: read + conditional-exec
  own u+rwX,g+rwX,o+rX "$TARGET"
done

# ————————————————————
# 1) Ontologies & media setup
# ————————————————————
ONT_DIR=/home/appuser/app/ontologies
if [ ! -d "$ONT_DIR/oeo" ]; then
  echo "Downloading ontology…"
  mkdir -p "$ONT_DIR"

  wget -qO /tmp/ont.zip \
    https://github.com/OpenEnergyPlatform/ontology/releases/latest/download/build-files.zip

  unzip -q /tmp/ont.zip -d "$ONT_DIR"
  rm /tmp/ont.zip

  own u+rwX,g+rwX,o+rX "$ONT_DIR"
fi

MEDIA_DIR=/home/appuser/app/media/oeo_ext
if [ ! -f "${MEDIA_DIR}/oeo_ext.owl" ]; then
  echo "Copying empty template…"
  mkdir -p "$MEDIA_DIR"
  cp /home/appuser/app/oeo_ext/oeo_extended_store/oeox_template/oeo_ext_template_empty.owl \
     "$MEDIA_DIR/oeo_ext.owl"

  # fix perms on the new file
  own u+rwX,g+rwX,o+rX "$MEDIA_DIR"
fi

# ————————————————————
# 2) Default securitysettings
# ————————————————————
SEC=/home/appuser/app/oeplatform/securitysettings.py
SEC_DEF=/home/appuser/app/oeplatform/securitysettings.py.default
if [ ! -f "$SEC" ]; then
  echo "Copying default securitysettings…"
  cp "$SEC_DEF" "$SEC"
  own u+rwX,g+rwX,o+rX "$SEC"
fi

# ————————————————————
# 3) OEKG shape artifacts
# ————————————————————
# The SHACL shape and the OEO label subset the OEKG API validates against.
# Needs the ontology from step 1 (the label subset is generated from it) and
# securitysettings from step 2 (manage.py will not import without it). Guarded
# like the ontology so a dev boot does not depend on GitHub every time; after
# bumping OEKG_SHAPES_PINNED_COMMIT in settings.py, re-run
# "python manage.py fetch_oekg_shapes" by hand or delete this directory.
SHAPES_DIR=/home/appuser/app/shapes
if [ ! -f "$SHAPES_DIR/oekg_shapes.ttl" ]; then
  echo "Fetching OEKG shape artifacts…"
  python manage.py fetch_oekg_shapes

  own u+rwX,g+rwX,o+rX "$SHAPES_DIR"
fi

# ————————————————————
# 4) Migrations
# ————————————————————
echo "Applying Django migrations…"
python manage.py migrate --no-input

echo "Applying Alembic migrations…"
python manage.py alembic upgrade head

# ————————————————————
# 5) Static & compress
# ————————————————————
echo "Collecting static files…"
python manage.py collectstatic --no-input

echo "Compressing assets…"
python manage.py compress --force

# ————————————————————
# 6) Create dev user
# ————————————————————
DEV_USER=test
DEV_PW=pass
echo "Ensuring dev user '$DEV_USER' exists…"
python manage.py create_dev_user "$DEV_USER" "$DEV_USER@mail.com" --password "$DEV_PW" || true
echo "✅  Dev user '$DEV_USER' password is: $DEV_PW"

# ————————————————————
# 7) Create a example table
# ————————————————————
echo "Seeding DataEdit tables…"
python manage.py create_example_tables

# ————————————————————
# 8) Launch dev server
# ————————————————————
echo "Starting Django dev server…"
exec "$@"
