# Install and setup the OpenEnergyPlatform Application

Below we describe the manual installation of the oeplatform code and infrastructure.
The installation steps have been proofed on linux and windows for python 3.6 and 3.9.

!!! tip
    We also offer the possibility to use [docker](https://www.docker.com/), to install the oeplatform and additional databases. As the hole setup is pre-configured docker can be used to automatically install the hole infrastructure.

    We provide 2 [docker container images](https://docs.docker.com/get-started/#what-is-a-container-image) (OEP-website and OEP-database). The images are updated & published with each release. They can be pulled from [GitHub packages](https://github.com/OpenEnergyPlatform/oeplatform/pkgs/container/oeplatform).

    [Here you can find instructions on how to install the docker images.](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/docker/USAGE.md)

!!! tip
    Use our Make script to automate most of the installation and setup process and get started in a simple and reusable way. Don't forget to familiarize yourself with the structure of the oeplattform architecture and know the credentials for each component (e.g. the user information of the databases).

    ``` bash
        make -f script/setup_and_migrate_db all
    ```

    !!! info "Only proven on Linux based systems."

??? Info "All steps & commands in one list"

    1. Get code & install dependencies.
        - `git clone https://github.com/OpenEnergyPlatform/oeplatform.git`
        - `cd oeplatform`
        - `python -m venv env`
        - `source env/bin/activate`
        - `pip install -r requirements.txt`

    2. Install databases & setup connection
        - Setup database 
        - Setup the connection to the database server to the Django project by adding the credentials in the `oeplatoform/securitysettings.py`

        ??? info "Option 1: Use docker"
            - [Install docker](https://docs.docker.com/get-docker/)
            - while in oeplatform directory `cd docker`
            - `docker compose -f docker-compose.yaml`
            - start docker container

        ??? info "Option 2: Manual database setup"
            - [install manually](./manual-db-setup.md)

    3. Setup the OEO integration
        - Instructions on [Section 4](#41-include-the-full-oeo)
    
    4. Run management commands
        - `python manage.py migrate`
        - python manage.py alembic upgrade head`
        - `python manage.py collectstatic`

        ??? Info "Sept 3.1: Additional commands" 
            These commands are not relevant if you are setting up oeplatform for the first time. One exception is the mirror command. If you have created some tables manually in the oedb database, you can use the mirror command to register them in the oeplatform.

            - `python manage.py mirror`
            - `python manage.py clear_sandbox`
            - `python manage.py clear_peer_reviews --all`


    5. Deploy locally
        - Check if the all connected database servers are running.
        - `python manage.py runserver`
        - Open Browser URL: 127.0.0.1:8000

        - [create a test user.](./development-setup.md#user-management)

## 1 Setup the repository

Clone the repository locally

```bash
git clone https://github.com/OpenEnergyPlatform/oeplatform.
git oep-website
```

Move to the cloned repository

    cd oep-website

## 2 Setup virtual environment

If you are a windows user, we recommend you use conda because of the dependency on the `shapely` package

    conda env create -f environment.yml

You can also use Python to create the environment

    python -m venv env

If you don't want to use conda, [here](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/) you can find instructions for setting up virtual environment

After you have activated your virtual environment, install the required python libraries

    pip install -r requirements.txt

## 3 Databases setup

We use two relational databases to store the oeplatform data:

- The oep-django database is our internal database. It is used to store the django application related data. This includes things like user information, reviews, table names, ...
- Our primary database is the OEDB (Open Energy Database). It is used to store all data the user uploaded. In production it stores multiple terabyte of data.

Additional we use a graph database:

- Store the open energy ontologies and open energy knowledge graph
- For now this is not part of the installation guide as it is not mandatory to run the oeplatform and can be added later.

### 3.1 How to install the databases

You have two options:

1. You chose to install the databases manually by installing PostgreSQL and complete the setup. In this case you can follow our [manual database setup guide](./manual-db-setup.md).

2. You can also use our docker based installation to install a container which will automatically setup the two databases. You still have to install docker on your system.
[Here you can find instructions on how to install the docker images.](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/docker/USAGE.md)

### 3.2 Create the database table structures

Before you can start development, you need to create all the tables in the two PostgreSQL databases. To do this, you can run two management commands. The django command will set up all the structures in the oep_django database and the alembic command will create all the structures in the OEDB.

### 3.2.1 Django setup - oep_django

In order to run the OEP website, the django database needs some extra management tables.
We use the django specific migrations. Each django app defines it own migrations that store all changes made to app related tabes. The table structure itself is defines the models for each django app.

    python manage.py migrate

### 3.2.2 Alembic setup - oedb

In order to run the OEP website, the primary database needs some extra management tables.
We use `alembic` to keep track of changes in those tables. To create all tables that are needed, simply type

    python manage.py alembic upgrade head

### 4 Setup the OpenEnergyOntology integation

#### 4.1 Include the full oeo

It is necessary to include the source files of the OpenEnergyOntology (OEO) in this project.
The goal is to setup a structure like you see below.

    ``` bash
    ontologies/
    └── oeo
        └── 1 # in production this will be the version of a specific OEO release
            ├── imports
            ├── modules
            └── oeo-full.owl
    ```

The root directory of the ontology folder (ontologies) is configured in the settings.py file for the oeplatform. The following variables are relevant for the configuration of the oeo directories. In most cases, you can use the default settings.

    ``` python
    ONTOLOGY_ROOT
    ONTOLOGY_FOLDER
    OPEN_ENERGY_ONTOLOGY_NAME
    OPEN_ENERGY_ONTOLOGY_FOLDER
    ```

If you use the default naming "ontology", you can download the full oeo release files from GitHub and unzip them into the directory. Check whether you can find the file "oeo-full.owl".

!!! info
    Download the [full oeo release from GitHub: Assets - build-files.zip](https://github.com/OpenEnergyPlatform/ontology/releases) and extract the oeo directory to match the pattern provided above.

    Get only the oeo `full-oeo.owl` from the [openenergyplatform.org](https://openenergyplatform.org/ontology/oeo/releases/oeo-full.owl)

#### 4.2 Setup the OEO-viewer app

!!! note "Optional Step"
    This step is not mandatory to run the oeplatform-core as it is a pluggable React-App. If you don't include this step you can access the oeplatform website including most ontology pages except for the oeo-viewer.

The oeo-viewer is a visualization tool for our OEO ontology and it is under development. To be able to see the oeo-viewer, follow the steps below:

1- Install npm:

- On linux: `sudo apt install npm`

- On MacOS: `brew install node`

- On windows see [here](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm).

2- Get the ontology files (see [Section 4.1](#41-include-the-full-oeo))

3- Build the oeo-viewer:

    cd oep-website/oeo_viewer/client
    npm install
    npm run build

After these steps, a `static` folder inside `oep-website/oeo_viewer/` will be created which includes the results of the `npm run build` command. These files are necessary for the oeo-viewer.

### 5 Setup the Scenario-Bundles app

!!! note "Optional Step"
    This step is not mandatory to run the oeplatform-core as it is a pluggable React-App. If you don't include this step you can access the oeplatform website except scenario-bundle pages including the scenario-comparison React modules.

In the django app directory `oeplatform/factsheet` we Provide a Web-API to access the OEKG and the Scenario-Bundle feature. Similar to the oeo-viewer we need to use npm to install & build the Scenario-Bundle app and integrate the build in the django app.

1. Make sure npm is installed.
2. Start the jenna-fuseki database (see [instructions](./manual-db-setup.md#12-install-apache-jena-fuseki) from the installation).

    The connection to the database API is setup in the factsheet/views.py you have to make sure that you provide the correct URL to you database instance. In developement mode it should be something like:

    ``` python
    query_endpoint = 'http://localhost:3030/ds/query'
    update_endpoint = 'http://localhost:3030/ds/update'
    ```

3. Configure the the React app:

    To be able to construct the API URLS that are necessary for communication between the react frontend and the django backend in the react code we have to configure the URL where our django application is available. In development mode this should be:

    `"toep": "http://127.0.0.1:8000/"`

    Add this line to `factsheet/frontend/src/conf.json`

4. Build the scenario bundle app:

    ``` bash
    cd factsheet/frontend
    npm install
    cd ../..
    # Use the django management command
    python manage.py build_factsheet_app
    ```

5. Serve the React build on a django website

    To serve the React build on a website that is provided by django you have to include the build files from the `factsheet/static` directory in the django template in `factsheet/templates/index.html`. In the html template the you must make sure that the JavaScript bundle file is imported. The name of the file changes after each new build and it should read like `main.5654a0e0.js`.

    The tamplate should then include this line:

    ```html
    <script src="{% static 'factsheet/js/main.55586e26.js' %}"></script>
    ```

## Next steps

Have a look at the steps described in the [Development & Collaboration](development-setup.md) section.
