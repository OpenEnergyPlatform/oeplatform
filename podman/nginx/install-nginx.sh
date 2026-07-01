#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Installs and configures the host nginx reverse proxy for the OEPlatform Podman
# stack. Idempotent — safe to re-run after config changes.
#
# The public domain is taken from OEP_URL in ~/.config/oeplatform/oep.env (the
# same value Django uses), so nothing needs to be edited by hand. You may also
# pass it explicitly as the first argument.
#
#   bash podman/nginx/install-nginx.sh                 # domain from oep.env
#   bash podman/nginx/install-nginx.sh my-domain.org   # domain from argument

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF_SRC="${SCRIPT_DIR}/oeplatform.conf"
ENV_FILE="${HOME}/.config/oeplatform/oep.env"
SITE=/etc/nginx/sites-available/oeplatform

# ── Resolve the domain: argument > OEP_URL in oep.env ────────────────────────
DOMAIN="${1:-}"
if [ -z "${DOMAIN}" ] && [ -f "${ENV_FILE}" ]; then
    DOMAIN="$(grep -E '^OEP_URL=' "${ENV_FILE}" | tail -1 | cut -d= -f2- | tr -d '"' | tr -d '[:space:]' || true)"
fi
if [ -z "${DOMAIN}" ] || [ "${DOMAIN}" = "127.0.0.1" ]; then
    echo "ERROR: no public domain found." >&2
    echo "Set OEP_URL in ${ENV_FILE} or pass the domain as the first argument." >&2
    exit 1
fi

echo "Configuring nginx reverse proxy for '${DOMAIN}'…"

# ── Install nginx if missing ─────────────────────────────────────────────────
if ! command -v nginx >/dev/null 2>&1; then
    echo "Installing nginx…"
    sudo apt-get update
    sudo apt-get install -y nginx
fi

# ── Install the site config with the domain substituted ──────────────────────
tmp="$(mktemp)"
sed "s/openenergyplatform\.example\.org/${DOMAIN}/g" "${CONF_SRC}" > "${tmp}"
sudo install -D -m 0644 "${tmp}" "${SITE}"
rm -f "${tmp}"

sudo ln -sf "${SITE}" /etc/nginx/sites-enabled/oeplatform
sudo rm -f /etc/nginx/sites-enabled/default   # drop the stock "Welcome" site

# ── Validate and reload ──────────────────────────────────────────────────────
sudo nginx -t
sudo systemctl reload nginx

echo ""
echo "Done. nginx is serving '${DOMAIN}' on :443 (plain HTTP — TLS terminated"
echo "upstream) and proxying to the container on 127.0.0.1:8080."
