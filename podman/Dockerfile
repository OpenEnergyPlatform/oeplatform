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

# Bake the OEO release and seed the OEO-extended store into the image BEFORE any
# manage.py command runs: ontology/apps.py OntologyConfig.ready() aborts Django
# startup — including the collectstatic/compress step below — unless these files
# exist. build-files.zip extracts to ontologies/oeo/<version>/… , the layout
# settings.py and ontology/views.py expect. -o overwrites any stale copy that
# COPY . /app pulled in from the build context (non-interactive build has no TTY
# to answer unzip's overwrite prompt).
RUN mkdir -p /app/ontologies /app/media/oeo_ext \
    && cd /app/ontologies \
    && wget -q https://github.com/OpenEnergyPlatform/ontology/releases/latest/download/build-files.zip \
    && unzip -qo build-files.zip \
    && rm build-files.zip \
    && cp -f /app/oeo_ext/oeo_extended_store/oeox_template/oeo_ext_template_empty.owl \
       /app/media/oeo_ext/oeo_ext.owl


# Build-time static asset collection (no DB needed)
# Compress is also run at build time since it only reads templates and static files
RUN cp /app/oeplatform/securitysettings.py.default /app/oeplatform/securitysettings.py \
    && python manage.py collectstatic --noinput \
    && python manage.py compress --force \
    && rm /app/oeplatform/securitysettings.py


EXPOSE 80

CMD ["/app/entrypoint.sh"]
