<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Installation

The oeplatform is more than the website: it runs with several databases, a
lookup service and the ontop service (see
[Infrastructure](../oeplatform-code/architecture/infrastructure.md)). There are
two ways to install all of it, depending on what you want to do.

<div class="grid cards" markdown>

- :material-laptop:{ .lg .middle } **Develop on your own computer**

  ***

  Run the whole platform locally with Docker Compose, with test data and a test
  user ready to use. Not for production.

  [:octicons-arrow-right-24: Development install (Docker)](guides/installation-docker-dev.md)

  Then set up git, your editor and the code checks:
  [Development setup](guides/development-setup.md)

- :material-server:{ .lg .middle } **Run the platform on a server**

  ***

  Deploy your own instance in production with rootless Podman and systemd
  Quadlets. This is the supported production path.

  [:octicons-arrow-right-24: Production deployment (Podman)](production-podman/index.md)

  Then give it your name, colours and logo:
  [Theming an instance](guides/instance-theming.md)

</div>

## Other guides

- [Development install (manual)](guides/installation.md), without Docker, step
  by step, if you want to see every part of the setup. It links the
  [detailed database setup](guides/manual-db-setup.md).
- [JavaScript integration](guides/nodejs.md): how the JavaScript apps are
  bundled.
