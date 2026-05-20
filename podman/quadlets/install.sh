#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Installs OEPlatform Quadlet units for the current user and reloads systemd.
# Run from the repository root:
#   bash podman/quadlets/install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUADLET_DIR="${HOME}/.config/containers/systemd"
ENV_DIR="${HOME}/.config/oeplatform"

echo "Installing Quadlet units to ${QUADLET_DIR}…"
mkdir -p "${QUADLET_DIR}"
cp "${SCRIPT_DIR}"/*.container "${QUADLET_DIR}/"
cp "${SCRIPT_DIR}"/*.volume    "${QUADLET_DIR}/"
cp "${SCRIPT_DIR}"/*.network   "${QUADLET_DIR}/"

if [ ! -f "${ENV_DIR}/oep.env" ]; then
    echo "Creating ${ENV_DIR}/oep.env from example…"
    mkdir -p "${ENV_DIR}"
    cp "${SCRIPT_DIR}/oep.env.example" "${ENV_DIR}/oep.env"
    echo ""
    echo "  !! Edit ${ENV_DIR}/oep.env and fill in all values before starting services."
fi

echo "Reloading systemd user daemon…"
systemctl --user daemon-reload

echo ""
echo "Done. Next steps:"
echo "  1. Edit ${ENV_DIR}/oep.env with real credentials (if not done yet)."
echo "  2. Pull the production images:"
echo "       podman pull ghcr.io/openenergyplatform/oeplatform-production:latest"
echo "       podman pull ghcr.io/openenergyplatform/oeplatform-ontop:latest"
echo "  3. Enable and start all services:"
echo "       systemctl --user enable --now oep-postgres oep-fuseki oep-oeplatform oep-ontop oep-lookup"
