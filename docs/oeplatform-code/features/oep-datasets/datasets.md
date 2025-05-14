<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>

SPDX-License-Identifier: CC0-1.0
-->

# Datasets

!!! danger "🚧 Feature not yet available"
    Datasets are still in development and not yet fully implemented as described below. Currently, tabular data resources are handled individually.

This section explains how we plan to implement **Datasets** in the OEP (Open Energy Platform).

## Context

The OEP is based on a relational database (PostgreSQL) and provides both a REST API and a user interface (UI) for reading, uploading, editing, and deleting data. This setup supports the **implementation phase** of research projects by enabling integrated, agile data management.

Our goal is to make data **reusable** and **comparable**, adding transparency to the complete data lifecycle. Many research projects struggle with data reusability and FAIR principles due to poor or missing data management workflows. We believe that by offering simple, flexible, and powerful tooling, we can change that.

The OEP integrates the **OpenEnergyDatabus**, which assigns persistent identifiers (PIDs) and versions to datasets. The Databus itself does not store data, but references it using semantic web technologies, [organizing data](https://dbpedia.gitbook.io/databus/model/how-to#general-structure) in a similar way to linked data graphs.

---

## About OEP Datasets

??? info "🧩 Dataset Specifications We Build On"
    Datasets are a general concept used to group one or more data resources. Each dataset represents a unique set of data resources, meaning resources are not duplicated within a dataset.

    Rather than being stored as a physical set in a database, datasets are often described using **metadata**. In most professional and governmental domains, datasets follow the **DCAT vocabulary** (W3C), particularly the **DCAT-AP** specification promoted by the EU.

    - 🔗 [DCAT Dataset Class Documentation](https://www.w3.org/TR/vocab-dcat-3/#Class:Dataset)

    Another popular framework is **Frictionless Data**, which offers:
    - A metadata specification for tabular datasets
    - A detailed schema for describing files like CSVs
    - Support for relational models (e.g., SQL tables)

On the OEP, datasets are accessible via the UI and programmatically via the REST API using standard HTTP methods.

---

## Use Cases

OEP Datasets serve multiple use cases:

**Draft Data Storage**

Upload data in any structure, using any PostgreSQL-supported types. No strict schema required during early exploration.

**Catalog Publishing**

Move draft datasets to published state within a topic category.

Requires:

- Open data license for each resource
- Consistent structure
- Metadata completeness

**Scenario Data**

Link datasets to **Scenario Bundles** for model comparison and scenario analysis.

This allows:

- Qualitative comparisons of scenario descriptions
- Quantitative comparisons using graphs and metrics across bundles

---

## Implementation

OEP Datasets are described using the **OEMetadata** specification. The metadata is stored as JSON on both the OEP and **MOSS**, our RDF-capable metadata store. MOSS handles:

- Generating RDF from JSON-LD
- Metadata search functionality

Keeping metadata in both systems improves integration but requires sync logic. This is solved by atomic updates on the OEP side when metadata is created or updated.

We organize datasets hierarchically within the data catalog:

1. `Topics/` – catalog categories
2. `Topics/<topic>/Datasets/`
3. `Topics/<topic>/Datasets/<dataset>/`
4. `Topics/<topic>/Datasets/<dataset>/Resources/`
5. `Topics/<topic>/Datasets/<dataset>/Resources/<resource>/`

This structure ensures deep linking and intuitive access across the platform.

---

## UI Preview

The OEP interface will visualize datasets within a navigable catalog structure and provide editing capabilities for metadata and resources.

!!! tip "🌱 Coming Soon"
    The dataset interface is currently under active development. Feedback and suggestions are welcome as we evolve the feature!
