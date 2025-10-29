<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Installation

This section provides detailed information on how to install for development
purposes. We will also provide a more detailed guide on how to operate the
oeplatform for production use cases in the future. The guide covers the full
oeplatform software and its infrastructure which is composed of the website,
various databases, a lookup service and the ontop-vkg service (see
[Infrastructure](../oeplatform-code/architecture/infrastructure.md)). You will
find two main options to install everything:

1. A docker based deployment setup for local deployment (and soon for production
   deployment setups)
2. A "manual" step by step installation guide for the oeplatform-website and its
   main features. The guide is mainly for development and documents the details
   of the installation.

Production deployments without containerization solutions like docker tend to be
very specific and depend on your infrastructure.

You will also find information on which further setup steps which should which
either help with some common issues and help with writing well formatted and
quality checked code to get started with contributing to developments on the
oeplatform.

## Guides

### Installation for development purposes

[Automated Docker based installation guide for development](./guides/installation-docker-dev.md)

[Manual installation guide](./guides/installation.md)

[Details on the database infrastructure setup](./guides/manual-db-setup.md)

### Next steps to get started with development

[Good practice and guidelines to participate in the development of the oeplatform](./guides/development-setup.md)

[Understand the nodejs integration and asset bundler for optimized javascript app deployments](./guides/nodejs.md)
