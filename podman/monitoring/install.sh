#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Installs the monitoring units for the current user, beside the app's units
# from podman/quadlets/install.sh. Run from the repository root:
#   bash podman/monitoring/install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
QUADLET_DIR="${HOME}/.config/containers/systemd"
UNIT_DIR="${HOME}/.config/systemd/user"
ENV_DIR="${HOME}/.config/oeplatform"

if [ ! -f "${ENV_DIR}/oep.env" ]; then
    echo "Missing ${ENV_DIR}/oep.env: install the app first (podman/quadlets/install.sh)." >&2
    exit 1
fi

echo "Installing monitoring units…"
mkdir -p "${QUADLET_DIR}" "${UNIT_DIR}" "${HOME}/.local/state/oep-monitoring/textfile"
cp "${SCRIPT_DIR}"/quadlets/* "${QUADLET_DIR}/"
cp "${SCRIPT_DIR}"/usage/oep-mon-usage.service "${SCRIPT_DIR}"/usage/oep-mon-usage.timer "${UNIT_DIR}/"
sed -i "s|@@OEP_REPO@@|${REPO_ROOT}|g" "${QUADLET_DIR}"/oep-mon-*.container "${UNIT_DIR}/oep-mon-usage.service"

# The probes must send the host name Django accepts.
OEP_URL="$(sed -n 's/^OEP_URL=//p' "${ENV_DIR}/oep.env" | tail -1)"
if [ -z "${OEP_URL}" ]; then
    echo "OEP_URL is empty in ${ENV_DIR}/oep.env; the app probes would all fail." >&2
    exit 1
fi
sed "s|@@OEP_URL@@|${OEP_URL}|" "${SCRIPT_DIR}/blackbox/blackbox.yml" > "${ENV_DIR}/blackbox.yml"

if [ ! -f "${ENV_DIR}/monitoring.env" ]; then
    install -m 600 "${SCRIPT_DIR}/monitoring.env.example" "${ENV_DIR}/monitoring.env"
    echo "  !! Fill in ${ENV_DIR}/monitoring.env before starting."
fi

systemctl --user daemon-reload

echo ""
echo "Done. Next steps (docs: Production deployment (Podman) > Monitoring):"
echo "  1. Fill in ${ENV_DIR}/monitoring.env."
echo "  2. Create the read-only database role oep_monitoring with that password."
echo "  3. systemctl --user start oep-mon-prometheus oep-mon-grafana oep-mon-blackbox \\"
echo "       oep-mon-node oep-mon-podman oep-mon-postgres"
echo "     systemctl --user enable --now oep-mon-usage.timer"
