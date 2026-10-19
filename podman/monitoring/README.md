<!--
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Monitoring for the Podman deployment

Prometheus, Grafana and four exporters as Quadlet units beside the app's, plus
an hourly timer for usage figures. Install with
`bash podman/monitoring/install.sh`.

The guide is the docs page **Production deployment (Podman) → Monitoring**
([`docs/installation/production-podman/monitoring.md`](../../docs/installation/production-podman/monitoring.md)).

Pinned versions: Prometheus v3.15.0, Grafana 13.2.4, blackbox exporter v0.29.0,
node exporter v1.12.1, postgres exporter v0.20.1, podman exporter v1.21.2.
