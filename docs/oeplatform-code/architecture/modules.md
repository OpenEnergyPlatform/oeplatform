<!--
SPDX-FileCopyrightText: 2025 jh-RLI <jonas.huber@rl-institut.de>

SPDX-License-Identifier: CC0-1.0
-->

# Modules of the oeplatform software

This section describes the modules of the oeplatoform website software. As we use django modules are also called apps. Each modules describes a django app that provides all the backend functionality as well as the user interface for a specific area of the website.

## Overview

Each module represents a [Django App](https://docs.djangoproject.com/en/4.2/ref/applications/) and includes a specific functionality or area of the Open Energy Platform Website.

| Module     | Function                                                                                                                                                                                                                                           |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| oeplatform | - Configuration of the Django application<br>- Security-critical configuration such as connection data to a database                                                                                                                               |
| base       | - Basic structure for homepage and views in other components<br>- Mainly static content for textual description of OEP and research projects<br>- Contact form<br>- Legal information                                                              |
| api        | - Provision of the RESTful API<br>- Data management<br>- Generic and specific data queries using query parameters<br>- User permission querying                                                                                                    |
| login      | - User management<br>- Login system                                                                                                                                                                                                                |
| dataedit   | - Presentation of database contents<br>- Metadata management and annotation of ontology terms<br>- Data management via user interface<br>- Tag system<br>- Data visualization<br>- Data querying via user interface<br>- Open Peer Review for data |
| modelview  | - Creation and editing of various factsheets using a developed standard format in the form of a form<br>- Factsheet searching<br>- Tag system                                                                                                      |
| ontology   | - Integration of the Open Energy Ontology<br>- Presentation of the contents of OEO<br>- Descriptive contents about OEO and the development process                                                                                                 |
| oeo_viewer | - Open Energy Ontology visualization<br>- Open Energy Ontology search functionality<br>- Special feature: Integrated React application                                                                                                             |

In addition to Django apps, there are other components that serve specific functionalities within the system:

| Module          | Explanation                                                                                                                                                                                                                                |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| theming         | Configures the global design using Bootstrap5 and provides design components that are imported into the software components listed above. This is where the user-friendly and aesthetic presentation of the web application is configured. |
| oedb_datamodels | Implements database migration schemas used for migrating changes to the database (OEDB). These schemas are utilized by an imported software tool to manage all changes to the Open Energy Database from within the Django application.     |
