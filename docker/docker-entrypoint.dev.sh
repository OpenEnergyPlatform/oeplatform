#!/usr/bin/env bash
set -euo pipefail

# give Postgres a moment
sleep 5

# ----------------------------------------------------------------
# Bootstrap permissions on bind-mounted dirs so appuser can write
# ----------------------------------------------------------------
for d in ontologies media/oeo_ext static; do
  TARGET="/home/appuser/app/$d"

  # ensure the directory exists
  mkdir -p "$TARGET"

  # make appuser own it
  chown -R appuser:appgroup "$TARGET"

  # owner & group: read/write + conditional-exec (dirs executable,
  # files only if already marked) ; others: read + conditional-exec
  chmod -R u+rwX,g+rwX,o+rX "$TARGET"
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

  chown -R appuser:appgroup "$ONT_DIR"
  chmod -R u+rwX,g+rwX,o+rX "$ONT_DIR"
fi

MEDIA_DIR=/home/appuser/app/media/oeo_ext
if [ ! -f "${MEDIA_DIR}/oeo_ext.owl" ]; then
  echo "Copying empty template…"
  mkdir -p "$MEDIA_DIR"
  cp /home/appuser/app/oeo_ext/oeo_extended_store/oeox_template/oeo_ext_template_empty.owl \
     "$MEDIA_DIR/oeo_ext.owl"

  # fix perms on the new file
  chown appuser:appgroup "$MEDIA_DIR/oeo_ext.owl"
  chmod u+rw,g+rw,o+rX "$MEDIA_DIR"
fi

# ————————————————————
# 2) Default securitysettings
# ————————————————————
SEC=/home/appuser/app/oeplatform/securitysettings.py
SEC_DEF=/home/appuser/app/oeplatform/securitysettings.py.default
if [ ! -f "$SEC" ]; then
  echo "Copying default securitysettings…"
  cp "$SEC_DEF" "$SEC"
  chown appuser:appgroup "$SEC"
  chmod u+rw,g+rw,o+rX "$SEC"
fi

# ————————————————————
# 3) Migrations
# ————————————————————
echo "Applying Django migrations…"
python manage.py migrate --no-input

echo "Applying Alembic migrations…"
python manage.py alembic upgrade head

# ————————————————————
# 4) Static & compress
# ————————————————————
echo "Collecting static files…"
python manage.py collectstatic --no-input

echo "Compressing assets…"
python manage.py compress --force

# ————————————————————
# 5) Create dev user
# ————————————————————
DEV_USER=test
DEV_PW=pass
echo "Ensuring dev user '$DEV_USER' exists…"
python manage.py create_dev_user "$DEV_USER" "$DEV_USER@mail.com" --password "$DEV_PW" || true
echo "✅  Dev user '$DEV_USER' password is: $DEV_PW"

# ————————————————————
# 6) Create a example table
# ————————————————————
echo "Seeding DataEdit tables…"
python manage.py create_example_tables

# ————————————————————
# 7) Launch dev server
# ————————————————————
echo "Starting Django dev server…"
exec "$@"
