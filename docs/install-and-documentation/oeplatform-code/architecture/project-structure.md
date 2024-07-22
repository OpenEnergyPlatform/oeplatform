## Project directory

The tree structure you see below describes the structure of the oeplatform code project. In general it is a django (using version 3.2) project that maintains multiple django apps that either serve for the frontend UI of the oeplatform website or host our WEB-API´s like the REST-API or our OEKG-API which provide a interface to specific functionality that accesses the the different databases we maintain.

The tree also shows several configurations and text files for the django application itself and also the project tooling and management we use to operate, test, maintain and document the system as well as the software code. Some files are also used to provide specific information about the development and deployment process and some other files are used for the project presentation on GitHub.

In the following we will dive a bit deeper into the structure of the project. We aim to provide a general understanding of the different modules so that developers become enabled to get started with the development.

```plaintext
.oeplatform
├── .github         # GitHub test automation & repository configuration
│   └── ...
├── api             # Django app
│   └── ...
├── base            # Django app
│   └── ...
├── dataedit        # Django app
│   └── ...
├── docker          # Docker & docker-compose setup
│   └── ...
├── docs            # mkdocs based project & code documentation
│   └── ...
├── factsheet       # Django app with react frontend
│   └── ...
├── login           # Django app
│   └── ...
├── media           # All kinds of media data from app´s
│   └── ...
├── modelview       # Django app
│   └── ...
├── oedb_datamodels # Alembic migrations to manage the database structure
│   └── ...
├── oeo_viewer      # Django app with react frontend
│   └── ...
├── oeplatform      # Project configuration
│   └── ...
├── ontology        # Django app
│   └── ...
├── static          # statics from all apps are collected here
│   ├── CACHE
│   └── ...
├── theming         # The general oep design / styling and ui components
│   └── ...
├── versions        # Changelogs
│   ├── bumpversion.sh
│   └── changelogs
├── CITATION.cff
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── RELEASE_PROCEDURE.md
├── VERSION
├── alembic.ini
├── mkdocs.yml
├── package-lock.json
├── tox.ini
├── manage.py
├── environment.yml
├── requirements-dev.txt
├── requirements-docs.txt
└── requirements.txt
```

## oeplatform

### Django Apps

Casual django app

```plaintext
├── dataedit
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── helper.py
│   ├── management
│   ├── metadata
│   ├── migrations
│   ├── models.py
│   ├── static
│   ├── structures.py
│   ├── templates
│   ├── templatetags
│   ├── tests.py
│   ├── urls.py
│   └── views.py
```

Django app that integrates a react frontend

```plaintext
├── factsheet
│   ├── __init__.py
│   ├── frontend
│   ├── management
│   ├── migrations
│   ├── models.py
│   ├── static
│   ├── templates
│   ├── urls.py
│   └── views.py
```

Basic functionality

- base
- login

REST API and Advanced API

- api

Features

Data publication(upload tabular data & metadata), view, search, peer-review, download

- dataedit

Model and Framework factsheets

- modelview

Scenario Bundles & Scenario Comparison

- factsheet

Integration of the OpenEnergyOntology (view, search download full .owl file that includes the latest release of the oeo)

- ontology

### Design

- base
- theming
- oep design system and workflow

```plaintext
├── theming
│   ├── Dockerfile
│   ├── README.md
│   ├── _variables.scss
│   ├── buildTheme.sh
│   ├── oepstrap.scss
│   └── scss
```

### Django-Project configuration

```plaintext
├── oeplatform
│   ├── __init__.py
│   ├── dumper.py
│   ├── securitysettings.py
│   ├── securitysettings.py.default
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   └── wsgi.py
```

- django models & migrations
- sqlalchemy alembic structures

### oedatabase

```plaintext
├── oedb_datamodels
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions
```

### oep django db

### oe knowledgegraph

### oe knowledgebase

## lookup oep

## test oeplatform (replication)

### Dev-opperations

- github actions
- automated tests
- workflows and procedure
- requirement management
- versions

### Collaboration

### Documentation

```plaintext
├── docs
│   ├── css
│   ├── dev
│   ├── index.md
│   └── install-and-documentation
```

```plaintext
├── docker
│   ├── Dockerfile
│   ├── USAGE.md
│   ├── apache2.conf
│   ├── docker-compose.yaml
│   └── docker-entrypoint.sh
```
