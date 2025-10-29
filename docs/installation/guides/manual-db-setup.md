# Complete manual database setup

Below we describe the complete manual installation of the OpenEnergyPlatform database infrastructure, which is currently composed by multiple databases:

1. PostgreSQL

   - Internal django database (oep_django)
   - as well as the primay database OpenEnergyDatabase (oedb)

2. Apache Jena Fuseki
   - and a SPARQL server for the OEKG
   - requires java

## 1 Install the database infrastructure

To setup the PostgreSQL database on your own machine you have to install the database software and setup additional packages. After the databases are installed you have to create the database tables that are already available as data model in the oeplatform code project. There we maintain the tables as python classes called models. You will use django and alembic to create these table automatically.

### 1.1 Install postgresql

If postgresql is not installed yet on your computer, you can follow this [guide](https://wam.readthedocs.io/en/latest/getting_started.html#installation-from-scratch).

Using linux it is most likely already installed. But you can use the following command to install it.

    sudo apt-get update
    sudo apt-get upgrade
    sudo apt-get install postgresql

During the installation, make sure that you note the superuser and password. Other relevant details are the host and the port, these will most likely be set to the default value. In the oeplatoform default configuration the values are:

- Host `127.0.0.1` or `localhost`.
- Port `5432`

For the creation of spatial objects we use the [PostGIS](https://postgis.net/install/) plugin for PostgreSQL. On linux you can use:

    sudo apt update
    sudo apt upgrade
    sudo apt install postgresql-14-postgis-3

    # might be relevant in some cases:
    # sudo apt-get install bin utils libproj-dev gdal-bin

??? Info "How to get PostGIS"

    PostGIS is a plugin for PostgreSQL and must be installed additionally. If you use an installation wizard, this step is probably included in the general PostgreSQL installation.

    - On Windows, We recommend installing the postgis for your local PostgreSQL installation from [Application Stack Builder](https://www.enterprisedb.com/edb-docs/d/postgresql/installation-getting-started/installation-guide-installers/9.6/PostgreSQL_Installation_Guide.1.09.html) under `Spatial Extensions`. There should automatically be an entry for `PostGIS bundle ...` based on the installed version of PostgreSQL, please make sure it is checked and click next. The stack builder will then continue to download and install PostGIS. Alternately PostGIS can also be downloaded from [this official ftp server](http://ftp.postgresql.org/pub/postgis/) by PostgreSQL. Proceed to install the package. (Flag it as safe in the downloads if prompted, and select Run anyway from the Windows SmartScreen Application Blocked Window)

    - On Linux/Unix based systems the installation could be specific to the package manager being employed and the operating system, so please refer to the official installation instructions [here](https://postgis.net/install/). The section `Binary Installers` covers the installation instructions for various operating systems.

After the installation completed you can start the service. On linux you can simply run:

    sudo service postgresql start

### 1.2 Install Apache Jena Fuseki

!!! note

    - Skip the installation if your development task is not aimed at the [OEKG](https://openenergyplatform.github.io/organisation/family_members/knowledge-representation/oekg/).
    - For more information about Apache Jena Fuseki please visit [this page.](https://jena.apache.org/documentation/fuseki2/)
    - Note that java is required to run the software

1.  Download [apache-jena-fuseki-4.2.0.tar.gz](https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-4.2.0.tar.gz)
    (for other versions please check [here](https://jena.apache.org/download/))
2.  Create a new directory on your system where you install oeplatform infrastructure components e.g. `~/oep-infra/` as alternative you can use the jenna-fuseki db via docker container. In this case you need to specify the correct credentails for that container in the `securitysettings.py` (See [Step 3.](#3-connect-database-to-the-django-project))
3.  Extract the downloaded file to the new directory e.g.:

        tar -zxvf apache-jena-fuseki-4.2.0.tar.gz -C ~/oep-infra/

4.  Navigate to the directory where the files are extracted and execute the following command to start the server:

        ./fuseki-server

5.  To access the server UI, enter `http://localhost:3030/` in your web browser.
6.  First click the **manage datasets** tab and then choose the **add new dataset**.
7.  Enter `OEKG_DS` for the **dataset name** and choose the type of dataset (in-memory datasets do not persist if the server stops) and click **create dataset**.

## 2 Create the PostgreSQL databases

As you dont have to setup the graph databse to run most parts of the oeplatform application and the PostgreSQL databases are mandatory for the core functionality of the oeplatform we start to setup the **oep_django** and **oedb** databases on our local PostgreSQL server.

### 2.1 Django internal database

#### 2.1.1 Posgresql command line setup

Once logged into your psql session from your terminal

- for linux: `sudo -u postgres psql`
- for windows: `psql`

then run the following lines to first set the database password as it will ease the further steps:

    ALTER USER postgres WITH PASSWORD 'postgres';

and then create the database:

    # optional: .. with owner = postgres;
    create database oep_django;

### 2.2 Primary Database

This database is used for the data input functionality implemented in `dataedit/`.

If this is your first local setup of the OEP website, this database should be an empty database as
it will be instantiated by automated scripts later on.

#### 2.2.1 Posgresql command line setup

Once logged into your psql session from your terminal

- for linux: `sudo -u postgres psql`
- for windows: `psql`

Then you run the following lines to create the primary database:

    # optional: .. with owner = postgres;
    create database oedb;

### 2.3 Install database extensions on both databases

After successfully installing PostGIS (see [step 1.1](#11-install-postgresql)), add the database extensions. We keep both database setups equal please enter the commands to both databases.

Make sure you connect to psql

    for linux: `sudo -u postgres psql`
    for windows: `psql`

`oedb` (`\c oedb;`) then create extensions.

`oep_django` (`\c oep_django;`) then create extensions also here.

After you connected type the commands below and repeat for both of the databases:

    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS postgis_topology;
    CREATE EXTENSION IF NOT EXISTS hstore;
    # This extension enable search for similar objects (e.g. by name)
    CREATE EXTENSION IF NOT EXISTS pg_trgm;

The database installation is now complete and you can exit the psql command line by typing:

    \q

## 3 Connect database to the Django project

In the oeplatform repository, copy the file `oeplatform/securitysettings.py.default` and rename it `oeplatform/securitysettings.py`. Then, enter the connection to your above mentioned postgresql database.

### 3.1 Store and access database credentials

To setup the connection in the oeplatform project you can either setup environment variables that store the database connection credentials locally on your system or you can change the default value in the securitysetting. For production systems it is recommended to use the concept of environment variables.

!!! Note

    You have to provide the user name and password (with access to the oep_django and oedb database). Additionally you can configure the database name and the host and port variables if you don't run the database server using the default values.

#### 3.1.1 oep_django internal database

In the oeplatform/securitysettings.py file enter the database connection details in this section:

!!! Info

    This code will attempt to collect the value from a environment variable in case it is not available the fallback value is used.

    `'NAME': os.environ.get("OEP_DJANGO_NAME", "oep_django")`

```python
# oeplatform/securitysettings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get("OEP_DJANGO_NAME", "oep_django"),
     'USER': os.environ.get("OEP_DJANGO_USER", "postgres"),
     'PASSWORD': os.environ.get("OEP_DJANGO_PW", "postgres"),
     'HOST': os.environ.get("OEP_DJANGO_HOST", "localhost")
 }
}

```

??? Note "Setup environment variables"

    Create environment variables `OEP_DJANGO_USER` and `OEP_DJANGO_PW` with values `oep_django_user` and `<oep_django_password>`, respectively.

    | environment variable | required |
    | -------------------- | -------- |
    | OEP_DJANGO_USER      | yes      |
    | OEP_DJANGO_PW        | yes      |
    | OEP_DJANGO_HOST      | no       |
    | OEP_DJANGO_NAME      | no       |

    For default settings, you can type the following commands

    - On windows
    We recommend you set the environment variables [via menus](https://www.computerhope.com/issues/ch000549.htm). However, we still provide you with the terminal commands (before you can set environment variables in your terminal you should first type `cmd/v`).

        ```bash
        set OEP_DJANGO_USER=oep_django_user
        set OEP_DJANGO_PW=<oep_django_password>
        ```

    In the following steps we'll provide the terminal commands but you always can set the environment variables via menus instead.

    - On linux

        ```bash
        export OEP_DJANGO_USER=oep_django_user
        export OEP_DJANGO_PW=<oep_django_password>
        ```

#### 3.1.2 oedb primary database

In the oeplatform/securitysettings.py file enter the database connection details in this section:

```python
# oeplatform/securitysettings.py

dbuser = os.environ.get("LOCAL_DB_USER", "postgres")
dbpasswd = os.environ.get("LOCAL_DB_PASSWORD", "postgres")
dbport = os.environ.get("LOCAL_DB_PORT", 5432)
dbhost = os.environ.get("LOCAL_DB_HOST", "localhost")
dbname = os.environ.get("LOCAL_DB_NAME", "oedb")
```

??? Note "Setup environment variables"

    | environment variable | required |
    | -------------------- | -------- |
    | LOCAL_DB_USER        | yes      |
    | LOCAL_DB_PASSWORD    | yes      |
    | LOCAL_DB_PORT        | no       |
    | LOCAL_DB_HOST        | no       |
    | LOCAL_DB_NAME        | no       |

    Make sure to set the required environment variables before going to the next section!

    For default settings, you can type the following commands

    - On windows

        ```bash
        set LOCAL_DB_USER=oedb_user
        set LOCAL_DB_PASSWORD=<oedb_password>
        set LOCAL_DB_NAME=oedb
        ```

    - On linux

        ```bash
        export LOCAL_DB_USER=oedb_user
        export LOCAL_DB_PASSWORD=<oedb_password>
        export LOCAL_DB_NAME=oedb
        ```

    !!! Tip
    
        If you kept the default name from the above example in 2.1, then the environment variables
        `LOCAL_DB_USER` and `LOCAL_DB_NAME` should have the values `oedb_user` and `oedb`, respectively.

## 4 Create the database tables

To complete the database installation, the table structures must then be installed. [Step 3](./installation.md#3-setup-the-openenergyontology-integration) & [Step 4](./installation.md#4-loading-and-compressing-static-assets-from-the-oeplattform-applications) must be completed first so that the necessary commands can be executed after.

After that Proceed with the next steps in section [4.2 Create the database table structures](installation.md#52-create-the-database-table-structures) of the oeplatform installation guide.
