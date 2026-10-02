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
SITE=/etc/nginx/sites-available/oeplatform

# Use sudo only when not already root, so this works both as a sudo-capable
# user (e.g. the container user) and when launched as root via `sudo bash …`
# by a separate admin account.
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    SUDO="sudo"
fi

# ── Resolve the domain: argument > OEP_URL in oep.env ────────────────────────
# When run via sudo, ${HOME} is root's home, so also look under the invoking
# user's home ($SUDO_USER) for oep.env.
DOMAIN="${1:-}"
if [ -z "${DOMAIN}" ]; then
    for env_file in "${HOME}/.config/oeplatform/oep.env" \
                    "${SUDO_USER:+/home/${SUDO_USER}/.config/oeplatform/oep.env}"; do
        if [ -n "${env_file}" ] && [ -f "${env_file}" ]; then
            DOMAIN="$(grep -E '^OEP_URL=' "${env_file}" | tail -1 | cut -d= -f2- | tr -d '"' | tr -d '[:space:]' || true)"
            [ -n "${DOMAIN}" ] && break
        fi
    done
fi
if [ -z "${DOMAIN}" ] || [ "${DOMAIN}" = "127.0.0.1" ]; then
    echo "ERROR: no public domain found." >&2
    echo "Set OEP_URL in ~/.config/oeplatform/oep.env or pass the domain as the first argument." >&2
    exit 1
fi

echo "Configuring nginx reverse proxy for '${DOMAIN}'…"

# ── Install nginx if missing ─────────────────────────────────────────────────
if ! command -v nginx >/dev/null 2>&1; then
    echo "Installing nginx…"
    ${SUDO} apt-get update
    ${SUDO} apt-get install -y nginx
fi

# ── Ensure a TLS certificate exists (self-signed unless one is provided) ─────
# nginx terminates TLS on :443; the upstream Apache proxy re-encrypts to it.
# Drop a real cert at these paths to replace the self-signed one.
CERT_DIR=/etc/nginx/ssl/oeplatform
if ! ${SUDO} test -f "${CERT_DIR}/fullchain.pem" || ! ${SUDO} test -f "${CERT_DIR}/privkey.pem"; then
    echo "Generating self-signed certificate for '${DOMAIN}'…"
    INTERNAL_FQDN="$(hostname -f 2>/dev/null || hostname)"
    ${SUDO} mkdir -p "${CERT_DIR}"
    ${SUDO} openssl req -x509 -nodes -days 825 -newkey rsa:2048 \
        -keyout "${CERT_DIR}/privkey.pem" \
        -out "${CERT_DIR}/fullchain.pem" \
        -subj "/CN=${DOMAIN}" \
        -addext "subjectAltName=DNS:${DOMAIN},DNS:${INTERNAL_FQDN},DNS:localhost,IP:127.0.0.1"
    ${SUDO} chmod 600 "${CERT_DIR}/privkey.pem"
fi

# ── Install the site config with the domain substituted ──────────────────────
tmp="$(mktemp)"
sed "s/openenergyplatform\.example\.org/${DOMAIN}/g" "${CONF_SRC}" > "${tmp}"
${SUDO} install -D -m 0644 "${tmp}" "${SITE}"
rm -f "${tmp}"

${SUDO} ln -sf "${SITE}" /etc/nginx/sites-enabled/oeplatform
${SUDO} rm -f /etc/nginx/sites-enabled/default   # drop the stock "Welcome" site

# ── Validate and reload ──────────────────────────────────────────────────────
${SUDO} nginx -t
${SUDO} systemctl reload nginx

echo ""
echo "Done. nginx terminates TLS on :443 for '${DOMAIN}' and proxies to the"
echo "container on 127.0.0.1:8080. The upstream Apache proxy re-encrypts to here."
