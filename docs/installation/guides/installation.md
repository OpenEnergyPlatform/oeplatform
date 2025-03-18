# Install and setup the OpenEnergyPlatform Application

Below we describe the manual installation of the oeplatform code and infrastructure.

!!! tip
    We also offer the possibility to use [docker](https://www.docker.com/), to install the oeplatform and additional databases. As the hole setup is pre-configured docker can be used to automatically install the hole infrastructure.

    We provide 2 [docker container images](https://docs.docker.com/get-started/#what-is-a-container-image) (OEP-website and OEP-database). The images are updated & published with each release. They can be pulled from [GitHub packages](https://github.com/OpenEnergyPlatform/oeplatform/pkgs/container/oeplatform).

    [Here you can find instructions on how to install the docker images.](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/docker/USAGE.md)

!!! danger
    Currently the docker based installation does not cover the installation of the additional database `jenna-fuseki` a triple store that stores graph data used in some of our features.
    It is not mandatory to run the core functionality of the oeplatform. You need to install it manually as described in the installation guide.


<!-- !!! tip
    Use our Make script to automate most of the installation and setup process and get started in a simple and reusable way. Don't forget to familiarize yourself with the structure of the oeplattform architecture and know the credentials for each component (e.g. the user information of the databases).

    ```bash
        make -f script/setup_and_migrate_db all
    ```

    !!! info "Only proven on Linux based systems." -->

??? Info "All steps & commands in one list"

    This list of commands will only work on systems where the core system dependencies
    already exists. Please use the full installation guide in case you encounter errors.

    1. Get code & install dependencies.
        - `git clone https://github.com/OpenEnergyPlatform/oeplatform.git`
        - `cd oeplatform`
        - Install python 3.10.
        - `python -m venv env`
        - `source env/bin/activate`
        - `pip install -r requirements.txt`

    2. Setup the OEO integration
        - Instructions on [Section 4](#41-include-the-full-oeo)
        - Automatically added in docker container

    3. Loading and compressing static assets
        - Create your `securitysettings.py` config file from our default settings: Copy & rename `oeplatform/securitysettings.py.default` >  `securitysettings.py`
        - `python manage.py collectstatic`
        - `python manage.py compress`
        - These steps are automatically added in the docker container

    4. Install databases & setup connection
        - Chose option 1 to use docker to install PostgreSQL and most of the setup automatically. You need to install jenna-fuseki additionally as it is not part of the docker container.
        - Chose 2 to install everything on your directly on your system.

        ??? info "Option 1: Use docker"
            - [Install docker](https://docs.docker.com/get-docker/)
            - while in oeplatform directory `cd docker`
            - `docker compose -f docker-compose.yaml`
            - start docker container
            - Additionally install and start jenna-fuseki db as docker or install it locally.

        ??? info "Option 2: Manual database setup"
            - [install manually](./manual-db-setup.md)

        Summary:

        - Setup databases PostgreSQL, Jenna-Fuseki
        - Install & start Jenna-Fuseki and create datastore `OEKG_DS` via the web interface: http://127.0.0.1:3030/
        - Install PostgreSQL
        - Use db user `postgres` with password `postgres`:
        - Create databases: `oep_django`, `oedb`: `sudo -u postgres psql`
        - Install postgresql extensions `hstore`, `postgis`, `postgis_topology`, `pg_trgm`
        - Setup the connection to the database server to the Django project by adding the credentials in the `oeplatoform/securitysettings.py`

    5. Run management commands to complete the database setup
        - `python manage.py migrate`
        - `python manage.py alembic upgrade head`

        ??? Info "Sept 3.1: Management commands:"
            These commands are most likely not relevant if you are setting up oeplatform for the first time. Use the following command to show a list of all available management commands.

            - `python manage.py -h`

    6. Install react app

        - Install node oder nvm on your system
        - navigate into `factsheet/frontend` to install the scenario bundles
        - navigate into the `oeo_viewer/client` to install the oeo viewer
        - Run `npm install`
        - Navigate back `cd ../..` to oeplatform root
        - Make sure the jenna-fuseki database is up and running locally
        - Run management commands to install bot react apps
            - `python manage.py build_factsheet_app`
            - `python manage.py build_oeo_viewer`
        - Update the served javaScript bundle files in templates:
            - `factsheet/static/js/main###.js` -> `factsheet/template/index.html`
            - `oeo_viewer/static/js/main###.js` -> `oeo_viewer/template/index.html`

    7. Deploy locally
        - Check if the all connected database servers are running.
            - sudo service postgresql start
            - in the directory where you installed

        - `python manage.py runserver`
        - Open Browser URL: 127.0.0.1:8000

        - [create a test user.](./development-setup.md#user-management-setup-a-test-user)

## 0 Prequisit

The installation instructions mainly refer to the creation of a local instance of the oeplatform with a focus on the development or contribution to the software development on github. We use mainly linux and sometimes windows for development with python 3.10 currently (Python 3.12 is also tested with some tweaks in the requirements.txt). Before you start the installation look at [this section](./development-setup.md#choose-your-development-environment-and-tools) and think about which operating system you want to use.

Deploying the software on a server to make it publicly accessible via the Internet is a further step. Please get in touch as the deployment depends heavily on your server setup.

### Notes for deployment

We do not currently provide instructions for deployment. It also depends heavily on the server environment. In general, a web server (e.g. [Apache](https://httpd.apache.org/)) and a [web server gateway for Python](https://peps.python.org/pep-3333/) (e.g. [mod_wsgi](https://modwsgi.readthedocs.io/en/master/)) are required to make the software available on the internet.

## 1 Setup the repository

Recommended: Create a directory to store the oeplatform code and additional resources.

    mkdir oep-website
    cd oep-website

Clone the repository locally

```bash
git clone https://github.com/OpenEnergyPlatform/oeplatform.git
```

## 2 Setup virtual environment

Navigate to the oeplatform directory you just cloned

    cd oeplatform

Below we explain two methods to install the virtual environment for python.

### Conda (on Windows)
If you are a Windows user, we recommend you use conda because of the dependency on the `shapely` package. It was causing installation issues that potentially have resolved. Don't forget to activate the environment after the setup is done.

    conda env create -f environment.yml
    conda activate env

### venv (on Linux / Mac)
If you are not using windows or don't want to use conda, [here](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/) you can find instructions for setting up virtual environment. In short: You can also use Python to create the environment. Make sure you install the venv package for your python version. Don't forget to activate the environment.

On linux you can use:

    sudo apt install python3.xx-venv # change xx to your exact version
    python3 -m venv env
    source env/bin/activate

### Install requirements
After you have activated your virtual environment, install the required python libraries

    pip install -r requirements.txt

## 3 Setup the OpenEnergyOntology integration

### 3.1 Include the full oeo

It is necessary to include the source files of the OpenEnergyOntology (OEO) in this project.
The goal is to have a new directory like you see below inside the oeplatform directory. The new folder should be stored alongside the django apps and other code related files.

    ```bash
    ontologies/
    └── oeo
        └── 1.0.0 # in production this will be the version of a specific OEO release
            ├── imports
            ├── modules
            └── oeo-full.owl
    ```

The directory where all ontologies are stored is called "ontologies". If you want to change the name of the directory you have to update the settings.py file for the oeplatform also. The following variables are relevant for the configuration of the ontology integration. In most cases, you can use the default settings.

```py
ONTOLOGY_FOLDER # Name of the folder for all ontologies
ONTOLOGY_ROOT   # constructed Path for all ontologies
OPEN_ENERGY_ONTOLOGY_NAME   # Name of the oeo
OPEN_ENERGY_ONTOLOGY_FOLDER # constructed Path for the oeo directory
```

If you use the default naming "ontologies" you should create this directory. Then you can download the [full oeo release from GitHub](https://github.com/OpenEnergyPlatform/ontology/releases) and unzip them into the new directory. To validate you can check whether you can find the file "oeo-full.owl". Please ensure, that you get the structure shown above.

## 4 Loading and compressing static assets from the Oeplattform applications

Static data is often stored in the django apps and various additional scripts are loaded, e.g. in HTML files. To enable django to access these resources more efficiently, various management commands are used to collect and partially compress the relevant files.

To be able to run the commands below we first need to Setup the security settings file for local development. This file is specific to your local settings. In production environment it is used to store / retrieve critical information that must not be pushed to any publicly available source control system like GitHub.

- Navigate to `oeplatform/oeplatform`
- copy the file `securitysettings.py.default` and rename it to `securitysettings.py`

??? note "How to configure securitysettings.py"
    The security settings provide information to django to connect to your databases, relevant for step 5, below. You can provide the access credentials directly in the script or import them using environment variables. For detailed instructions see section [3. of the manual database setup guide](./manual-db-setup.md#3-connect-database-to-the-django-project).

After the above setup is done make sure the python environment is activated and then run:

    python manage.py collectstatic
    python manage.py compress

## 5 Databases setup

We use two relational databases to store the oeplatform data:

- The oep-django database is our internal database. It is used to store the django application related data. This includes things like user information, reviews, table names, ...
- Our primary database is the OEDB (Open Energy Database). It is used to store all data the user uploaded. In production it stores multiple terabyte of data.

Additional we use a triple store database:

- Store the open energy ontologies and open energy knowledge graph
- For now this is not part of the installation guide as it is not mandatory to run the oeplatform and can be added later.

### 5.1 How to install the databases

You can install the database and connect it to django as you like. Note that we currently use PostgreSQL version 14.

Below we offer our best practice to setup the databases. You have two options to install the databases:

#### a) Install the database manually
   * You chose to install the databases manually by installing PostgreSQL & jenna-fuseki and complete the setup. In this case you can follow our [manual database setup guide](./manual-db-setup.md).
   * Using this option you will install the jenna-fuseki & postgresql databases on your local system. You need to start both databases manually before you can start using them for development.

#### b) Use our docker image
   * You can also use our docker based installation to install a container which will automatically setup the two databases. You still have to install docker on your system. [Here you can find instructions on how to install the docker images.](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/docker/USAGE.md)
   * The jenna-fuseki triple store is not part of the docker image so far. You would either have to setup the public docker image here and adjust the credentials in the `securitysettings.py` or you can perform the steps explained in [Section 1.2 of the manual database setup](./manual-db-setup.md#12-install-apache-jena-fuseki) to install the jenna-fuseki database on your system. You will have to start the service manually afterwards.

### 5.2 Create the database table structures

Before you can start development, you need to setup tables in the two PostgreSQL databases. To do this, you can run two management commands. The django command will set up all structures required by the oep system in the oep_django database and the alembic command will create all the structures in the OEDB. These structures define how large amounts of uploaded user data is stored in the database. On a high level this is similar to partitions on you personal computer. This structure help's the developers and the system to find the data and group data together.

First verify that your database service is running. In case you are using docker start the container. If you installed postgresql locally start the service. On Linux you can use the following command in the terminal:

    sudo service postgresql start

### 5.2.1 Django setup - oep_django

In order to run the OEP website, the django database needs some extra management tables.
We use the django specific migrations. Each django app defines it own migrations that keep track of all changes made to any app related tabes. The table structure itself is defined as an abstraction in the models.py for each django app.

    python manage.py migrate

### 5.2.2 Alembic setup - oedb

In order to run the OEP website, the primary database needs some extra management tables.
We use `alembic` to keep track of changes to the general structure of the primary database and its initial state e.g. what tables should be there and more. To create all tables that are needed, simply type:

    python manage.py alembic upgrade head

!!! Note
    If you encounter errors in this step verify that your database service is available, the databases `oep_django` and `oedb` exist and your `securitysettings.py` provide the correct access credentials.

## 6 Install the OpenEnergyOntology tools

Only start the following steps if you have completed step 3 above.

### 6.1 Setup the OEO-viewer app

!!! note "Optional Step"
    This step is not mandatory to run the oeplatform-core as it is a plug able React-App. If you don't include this step you can access the oeplatform website including most ontology pages except for the oeo-viewer.

The oeo-viewer is a visualization tool for our OEO ontology and it is under development. To be able to see and use the oeo-viewer as part of the oep-website, follow the steps below:

1. Install npm:
   To install npm it is suggested to use the node version manager.
     - On Linux & Mac:  [Node Version Manager (nvm)](https://github.com/nvm-sh/nvm)
     - On Windows: [NVM for Windows](https://github.com/coreybutler/nvm-windows).
     - Install node version 18
2. Get the ontology files (see [Section 3](#3-setup-the-openenergyontology-integration))

3. Build the oeo-viewer:
    ```
    cd oep-website/oeplatform/oeo_viewer/client
    npm install
    npm run build
    ```

After these steps, a `static` folder inside `oep-website/oeplatform/oeo_viewer/` will be created which includes the results of the `npm run build` command. These files are necessary for the oeo-viewer.

### 6.2 Setup the oeo extended app

The oeo extended is used to create new ontology classes on the fly while annotating a oemetadata document. Especially if one wants to annotate composed units which are more complex than a simple meter or square meter unit. These composed units are stored separate from the OEO ontology in the OEOX which is located in its own owl file.

The use case described above requires to setup the oeo extended template file in the `media/` directory. We offer a template file to simplify this task.

    cp oeo_ext/oeo_extended_store/oeox_template/oeo_ext_template_empty.owl  media/oeo_ext/oeo_ext.owl

## 7 Setup the Scenario-Bundles app

!!! note "Optional Step"
    This step is not mandatory to run the oeplatform-core as it is a plug able React-App. If you don't include this step you can access the oeplatform website except scenario-bundle pages including the scenario-comparison React modules.

In the django app directory `oeplatform/factsheet` we provide a Web-API to access the OEKG and the Scenario-Bundle feature. Similar to the oeo-viewer we need to use npm to install & build the Scenario-Bundle app and integrate the build in the django app.

1. Make sure npm is installed.
2. Start the jenna-fuseki database (see [instructions](./manual-db-setup.md#12-install-apache-jena-fuseki) from the installation).
   The connection to the database API is setup in the factsheet/views.py you have to make sure that you provide the correct URL to you database instance. In development mode it should be something like:
   ```py
   query_endpoint = 'http://localhost:3030/ds/query'
   update_endpoint = 'http://localhost:3030/ds/update'
   ```

3. Configure the React app

     To be able to construct the API URLS that are necessary for communication between the react frontend and the django backend in the react code we have to configure the URL where our django application is available. In development mode this should be http://127.0.0.1:8000/, so add the line `"toep": "http://127.0.0.1:8000/"` to `factsheet/frontend/src/conf.json`.

4. Build the scenario bundle app:
      ```
      cd factsheet/frontend
      npm install
      cd ../..
      # Use the django management command
      python manage.py build_factsheet_app
      ```

5. Serve the React build on a django website

     To serve the React build on a website that is provided by django you have to include the build files from the `factsheet/static` directory in the django template in `factsheet/templates/index.html`. In the HTML-template you must make sure that the JavaScript bundle file is imported. The name of the file changes after each new build and it should read like `main.5654a0e0.js`.

     The template should then include this line:

     ```html
     <script src="{% static 'factsheet/js/main.55586e26.js' %}"></script>
     ```

## Next steps

Have a look at the steps described in the [Development & Collaboration](development-setup.md) section.
