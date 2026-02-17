#!/usr/bin/env bash
set -euo pipefail

# give Postgres a moment
sleep 5

# ================================================================
# WINDOWS COMPATIBILITY CHECK (ohne tatsächliche chown-Ausführung)
# ================================================================
SKIP_PERMS=""

# Method 1: Try a harmless chown on /tmp (always works on real Linux)
if ! touch /tmp/chown-test && chown $(id -u):$(id -g) /tmp/chown-test 2>/dev/null; then
  rm -f /tmp/chown-test 2>/dev/null
  echo "🐧 Linux environment detected → Full permission management enabled"
else
  echo "🪟 Windows/Docker Desktop detected → Permission operations will be skipped"
  SKIP_PERMS="1"
  rm -f /tmp/chown-test 2>/dev/null
fi

# ----------------------------------------------------------------
# Bootstrap permissions on bind-mounted dirs so appuser can write
# ----------------------------------------------------------------
for d in ontologies media/oeo_ext static; do
  TARGET="/home/appuser/app/$d"

  # ensure the directory exists
  mkdir -p "$TARGET"

  # Only do chown/chmod if not on Windows
  if [ -z "$SKIP_PERMS" ]; then
    # make appuser own it
    chown -R appuser:appgroup "$TARGET" 2>/dev/null || true
    # owner & group: read/write + conditional-exec
    chmod -R u+rwX,g+rwX,o+rX "$TARGET" 2>/dev/null || true
  fi
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

  # WINDOWS FIX: Use -X flag to suppress permission setting during unzip
  if [ -n "$SKIP_PERMS" ]; then
    # On Windows: Extract without trying to set permissions
    unzip -qX /tmp/ont.zip -d "$ONT_DIR" 2>/dev/null || unzip -q /tmp/ont.zip -d "$ONT_DIR"
  else
    # On Linux: Normal extraction
    unzip -q /tmp/ont.zip -d "$ONT_DIR"
    chown -R appuser:appgroup "$ONT_DIR" 2>/dev/null || true
    chmod -R u+rwX,g+rwX,o+rX "$ONT_DIR" 2>/dev/null || true
  fi
  
  rm /tmp/ont.zip
fi

MEDIA_DIR=/home/appuser/app/media/oeo_ext
if [ ! -f "${MEDIA_DIR}/oeo_ext.owl" ]; then
  echo "Copying empty template…"
  mkdir -p "$MEDIA_DIR"
  cp /home/appuser/app/oeo_ext/oeo_extended_store/oeox_template/oeo_ext_template_empty.owl \
     "$MEDIA_DIR/oeo_ext.owl"

  # Only do chown/chmod if not on Windows
  if [ -z "$SKIP_PERMS" ]; then
    chown appuser:appgroup "$MEDIA_DIR/oeo_ext.owl" 2>/dev/null || true
    chmod u+rw,g+rw,o+rX "$MEDIA_DIR" 2>/dev/null || true
  fi
fi

# ————————————————————
# 2) Default securitysettings - FIX für fehlende CORS_ORIGIN_ALLOW_ALL
# ————————————————————
SEC=/home/appuser/app/oeplatform/securitysettings.py
SEC_DEF=/home/appuser/app/oeplatform/securitysettings.py.default
if [ ! -f "$SEC" ]; then
  echo "Copying default securitysettings…"
  cp "$SEC_DEF" "$SEC"
  
  # WINDOWS FIX: Ensure CORS_ORIGIN_ALLOW_ALL is defined if missing
  if ! grep -q "CORS_ORIGIN_ALLOW_ALL" "$SEC"; then
    echo "" >> "$SEC"
    echo "# Windows compatibility fix" >> "$SEC"
    echo "CORS_ORIGIN_ALLOW_ALL = True" >> "$SEC"
  fi
  
  # Only do chown/chmod if not on Windows
  if [ -z "$SKIP_PERMS" ]; then
    chown appuser:appgroup "$SEC" 2>/dev/null || true
    chmod u+rw,g+rw,o+rX "$SEC" 2>/dev/null || true
  fi
else
  # File exists, but check if CORS_ORIGIN_ALLOW_ALL is missing
  if ! grep -q "CORS_ORIGIN_ALLOW_ALL" "$SEC"; then
    echo "Adding missing CORS_ORIGIN_ALLOW_ALL to existing securitysettings.py…"
    echo "" >> "$SEC"
    echo "# Windows compatibility fix" >> "$SEC"
    echo "CORS_ORIGIN_ALLOW_ALL = True" >> "$SEC"
  fi
fi

# ————————————————————
# 3) Migrations
# ————————————————————
echo "Applying Django migrations…"
python manage.py migrate --no-input

echo "Applying Alembic migrations…"
python manage.py alembic upgrade head

# ————————————————————
# 4) Static & compress - SKIP IN DEV ON WINDOWS
# ————————————————————
if [ -z "$SKIP_PERMS" ]; then
  echo "Collecting static files…"
  python manage.py collectstatic --no-input

  echo "Compressing assets…"
  python manage.py compress --force
else
  echo "⏭️  Skipping collectstatic/compress on Windows (Django will serve static files directly)"
fi

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
