<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Complete ontop setup

The PostgreSQL JDBC driver is **downloaded automatically** when the ontop image
is built — `docker/Dockerfile.ontop` fetches it from Maven Central and places it
on Ontop's classpath. No manual download is required.

To use a different driver version, build with:

```sh
podman build --build-arg JDBC_VERSION=42.7.3 \
  -t ghcr.io/openenergyplatform/oeplatform-ontop:latest \
  -f docker/Dockerfile.ontop docker/
```
