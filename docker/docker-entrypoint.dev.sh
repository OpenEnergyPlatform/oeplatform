#!/usr/bin/env bash
set -euo pipefail

# give Postgres a moment
sleep 5

# ————————————————————
# 1) Ontologies & media setup
# ————————————————————
ONT_DIR=/home/appuser/app/ontologies
if [ ! -d "$ONT_DIR" ]; then
  echo "Downloading ontology…"
  mkdir -p "$ONT_DIR"
  wget -qO- https://github.com/OpenEnergyPlatform/ontology/releases/download/v2.5.0/build-files.zip \
    | funzip > /tmp/ont.zip \
    && unzip -q /tmp/ont.zip -d "$ONT_DIR" \
    && rm /tmp/ont.zip
fi

MEDIA_DIR=/home/appuser/app/media/oeo_ext
if [ ! -f "${MEDIA_DIR}/oeo_ext.owl" ]; then
  echo "Copying empty template…"
  mkdir -p "$MEDIA_DIR"
  cp /home/appuser/app/oeo_ext/oeo_extended_store/oeox_template/oeo_ext_template_empty.owl \
     "$MEDIA_DIR/oeo_ext.owl"
fi

# ————————————————————
# 2) Default securitysettings
# ————————————————————
SEC=/home/appuser/app/oeplatform/securitysettings.py
SEC_DEF=/home/appuser/app/oeplatform/securitysettings.py.default
if [ ! -f "$SEC" ]; then
  echo "Copying default securitysettings…"
  cp "$SEC_DEF" "$SEC"
fi

# ————————————————————
# 3) Migrations
# ————————————————————
echo "Applying Django migrations…"
python manage.py migrate --no-input

echo "Applying Alembic migrations…"
python -m alembic upgrade head

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
echo "Ensuring dev user 'test' exists…"
python manage.py create_dev_user test test@mail.com --password pass || true

# ————————————————————
# 6) Launch dev server
# ————————————————————
echo "Starting Django dev server…"
exec "$@"
