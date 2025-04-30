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

??? info "OEP Datasets serve multiple use cases"

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

**User Stories overview**

- User want to create datasets and want to add data, delete data and tables from the dataset or edit it.
- User can use the UI of the Website and the Rest-API to do all datasets related tasks
- Users want to find data and publish it: Data is grouped in topics and all datasets are uploaded to the model_draft as a initial editing space, later datasets can be published and are considered complete, multiple versions might follow
- Users may want to add Datasets to multiple topics
- Users want to use well known functionality like the Legacy API functionality. They think that it cannot be changed suddenly.
(if we need to add functionality we want to make it optional. Once it was adopted we can start do bigger changes.)

---

## Implementation

??? info "Changes in OEP"

    First of we have in the OEP:

    - Two databases 1. Primary DB and 2. Django DB. The Datastore for actual data is the Primary DB and the Django DB is like data registry to manage uploaded datasets and provide additional functionality.

    - The django application in which mainly the `api` & `dataedit` apps are affected.

??? info "What other services are affected"

    Additionally we need to handle:

    - The Databus is the PID system for the OEP. Once the data is in a specific quality it is either manually or automatically (once published) registered on the Databus. The Databus itself only stores a metadata entry (based on DCAT-AP) in its internal graph store. It offers a rest api. It is hosted outside the OEP network but is connected internally to enable server-to-server communication.
    - The MOSS is another Service we want to use to provide extended semantic search functionality based on the oemetadata entires for each dataset/table. It will also serve as primary metadata store for the OEP. It is also connected to the OEP for server-to-server communication.

??? info "OEMetadata & Moss"

    OEP Datasets are described using the **OEMetadata** specification. The metadata is stored as JSON on both the OEP and **MOSS**, our RDF-capable metadata store. MOSS handles:

    - Primary store for metadata documents
    - Generating RDF from JSON-LD
    - Metadata search functionality

    Keeping metadata in both systems improves integration but requires sync logic. This is solved by atomic updates on the OEP side when metadata is created or updated both systems are updated or changes are ignored and the user is informed.

As described above we define a dataset similar to the DCAT-AP definition and build ontop of the frictionless datapackage standard. A datasets can be either a single table resource or multiple. We organize datasets hierarchically. All Datasets are grouped into Topics which make up the catalog categories. The Topics are not part of the hierarchy as datasets can be in multiple Topics.

With this baseline definition we get a desired hierarchy which looks like this:

1. `Datasets/`
2. `Datasets/<dataset>/`
3. `Datasets/<dataset>/Resources/`
4. `Datasets/<dataset>/Resources/<resource>/`

This structure ensures deep linking and intuitive access across the platform.

**What will change in the current URL/API system?**
(While keeping functionality available)

To keep the current functionality in place the previous per-table approach is maintained and current urls are redirected:

Topics will not be part of the dataset url anymore but there will be topic specific list urls like

1. `database/topics`            = list all topics
2. `database/topics/<topic>`    = list all datasets/tables per topic

Currently we have something like `topics/<topic>/tables/<table>` which will become

1. `datasets`           = Not necessarily relevant but for api request this could be an easy way to get all available datasets
2. `datasets/<table>/`  = Tables detail page

How this will affect the REST-API:

Since we already have a production implementation up and running since years and users are used to the existing structure as well as all REST-API endpoints using

---

## UI Preview

The OEP interface will visualize datasets within a navigable catalog structure and provide editing capabilities for metadata and resources.

!!! tip "🌱 Coming Soon"
    The dataset interface is currently under active development. Feedback and suggestions are welcome as we evolve the feature!
