#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -euo pipefail

# ── 1) Ontologies ─────────────────────────────────────────────────────────────
# Download the latest OEO release only on first start. The ontologies/ directory
# is a named volume so this survives container rebuilds.
ONT_DIR=/app/ontologies

if [ ! -d "${ONT_DIR}/oeo" ]; then
    echo "Downloading latest OEO release…"
    mkdir -p "${ONT_DIR}"
    wget -qO /tmp/oeo.zip \
        https://github.com/OpenEnergyPlatform/ontology/releases/latest/download/build-files.zip
    unzip -q /tmp/oeo.zip -d "${ONT_DIR}"
    rm /tmp/oeo.zip
    echo "OEO downloaded to ${ONT_DIR}"
else
    echo "OEO already present, skipping download."
fi

# ── 2) OEO extended ───────────────────────────────────────────────────────────
# Seed the empty template only when no oeo_ext.owl exists yet. The media/
# directory is a named volume, so the file persists across container restarts
# and rebuilds and will never be overwritten here.
OEO_EXT=/app/media/oeo_ext/oeo_ext.owl

if [ ! -f "${OEO_EXT}" ]; then
    echo "Seeding empty OEO-extended template…"
    mkdir -p /app/media/oeo_ext
    cp /app/oeo_ext/oeo_extended_store/oeox_template/oeo_ext_template_empty.owl "${OEO_EXT}"
    echo "OEO-extended template written to ${OEO_EXT}"
else
    echo "OEO-extended file already exists, skipping seed."
fi
# TODO: load oeo_ext.owl into Fuseki as a named graph so it is queryable via
# SPARQL alongside the base OEO. See GitHub issue #<TBD>.

# ── 3) Security settings ──────────────────────────────────────────────────────
SEC=/app/oeplatform/securitysettings.py
SEC_DEF=/app/oeplatform/securitysettings.py.default

if [ ! -f "${SEC}" ]; then
    echo "Copying default securitysettings…"
    cp "${SEC_DEF}" "${SEC}"
fi

# ── 4) Database migrations ────────────────────────────────────────────────────
echo "Applying Django migrations…"
python manage.py migrate --no-input

echo "Applying Alembic migrations…"
python manage.py alembic upgrade head

# ── 5) Start Apache ───────────────────────────────────────────────────────────
echo "Starting Apache…"
exec /usr/sbin/apache2ctl -DFOREGROUND
