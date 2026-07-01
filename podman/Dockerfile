# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# ── Stage 1: build Vite frontend assets ──────────────────────────────────────
FROM node:25.2.1 AS vite-build

WORKDIR /app

# Install deps first for better layer caching
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build
# Output: /app/assets/ (including manifest.json read by django-vite)


# ── Stage 2: production application ──────────────────────────────────────────
FROM python:3.10.14

RUN apt-get update \
    && apt-get install -y --no-install-recommends apache2 apache2-dev wget unzip \
    && rm -rf /var/lib/apt/lists/*

# Enable required Apache modules
RUN a2enmod headers

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt \
    && pip install mod_wsgi \
    && mod_wsgi-express module-config >> /etc/apache2/apache2.conf

COPY podman/apache2.conf /etc/apache2/conf-enabled/oeplatform.conf
COPY . /app

# Overwrite any local assets/ with the freshly built Vite output from stage 1
COPY --from=vite-build /app/assets /app/assets

COPY podman/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Volume mount points — created here so named volumes initialise correctly.
# The OEO release and oeo_ext.owl are NOT baked into the image; entrypoint.sh
# downloads/seeds them into the mounted named volumes on first container start
# (see podman/entrypoint.sh).
RUN mkdir -p /app/ontologies /app/media/oeo_ext

# Build-time static asset collection (no DB needed)
# Compress is also run at build time since it only reads templates and static files
RUN cp /app/oeplatform/securitysettings.py.default /app/oeplatform/securitysettings.py \
    && python manage.py collectstatic --noinput \
    && python manage.py compress --force \
    && rm /app/oeplatform/securitysettings.py


EXPOSE 80

CMD ["/app/entrypoint.sh"]
