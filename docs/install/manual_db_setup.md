# Complete manual database setup 

Below we describe the complete manual installation of the OpenEnergyPlatform database infrastructure, which is currently composed by multiple databases:

1. PostgreSQL
    - Internal django database (oep_django)
    - as well as the primay database OpenEnergyDatabase (oedb)


2. JennaFuseki 
    - and a graph database for the oeo and oekg



## 1 Install the database infrastructure

To setup the PostgreSQL database on your own machine your have to install the database software and setup additional packages as well as install the database tables that are already available as datamodel which is maintained as python classes called (data-) models. 

!!! tip
    We also offer the possibility to use [docker](https://www.docker.com/), if you are a developer you could manually install the OEP alongside the dockercontainer to run the database or run everything in docker. This can facilitate the maintenance of the Oeplattform infrastructure and the local deployment of the Oeplattform. However, Docker as additional software usually requires more resources, especially memory.
    
    For this purpose, 2 [docker container images](https://docs.docker.com/get-started/#what-is-a-container-image) (OEP-website and OEP-database) are published with each release, which can be pulled from [GitHub packages](https://github.com/OpenEnergyPlatform/oeplatform/pkgs/container/oeplatform).

    [Here you can find instructions on how to install the docker images.](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/docker/USAGE.md)
### Install postgresql

If postgresql is not installed yet on your computer, you can follow this [guide](https://wam.readthedocs.io/en/latest/getting_started.html#installation-from-scratch)

### Install JennaFuseki

!!! warning
    missing!

!!! note
        Skip the installation if your developement task is not aimed at the OpenEnergyOntology or the OEKnowlageGraph.

## 2 Create the PostgreSQL databases

As you dont have to setup the graph databse to run most parts of the oeplatform application and the PostgreSQL databases are mandatory for the core functionality of the oeplatform we start to setup the **oep_django** and **oedb** databases on our local PostgreSQL server.

### 2.1 Django internal database


#### 2.1.1 Posgresql command line setup

Once logged into your psql session (for linux: `sudo -u postgres psql`, for windows: `psql`), run the following lines:

    # optional: .. with owner = postgres;
    create database oep_django;

### 2.2 Primary Database

This database is used for the data input functionality implemented in `dataedit/`.

If this is your first local setup of the OEP website, this database should be an empty database as
it will be instantiated by automated scripts later on.

#### 2.2.1 Posgresql command line setup

Once logged into your psql session (for linux: `sudo -u postgres psql`, for windows: `psql`), run the following lines:

    # optional: .. with owner = postgres;
    create database oep_db;

For the creation of spatial objects we use [PostGIS](https://postgis.net/install/) for PostgreSQL.

!!! Info
    PostGIS is a plugin for PostgreSQL and must be installed additionally.


    - On Windows, We recommend installing the postgis for your local PostgreSQL installation from [Application Stack Builder](https://www.enterprisedb.com/edb-docs/d/postgresql/installation-getting-started/installation-guide-installers/9.6/PostgreSQL_Installation_Guide.1.09.html) under `Spatial Extensions`. There should automatically be an entry for `PostGIS bundle ...` based on the installed version of PostgreSQL, please make sure it is checked and click next. The stack builder will then continue to download and install PostGIS. Alternately PostGIS can also be downloaded from [this official ftp server](http://ftp.postgresql.org/pub/postgis/) by PostgreSQL. Proceed to install the package. (Flag it as safe in the downloads if prompted, and select Run anyway from the Windows SmartScreen Application Blocked Window)

    - On Linux/Unix based systems the installation could be specific to the package manager being employed and the operating system, so please refer to the official installation instructions [here](https://postgis.net/install/). The section `Binary Installers` covers the installation instructions for various operating systems.

After successfully installing PostGIS, enter in `oep_db` (`\c oep_db;`) and type the additional commands:

    create extension postgis;
    create extension postgis_topology;
    create extension hstore;


## 3 Connect database to the Django project

In the oeplatform repository, copy the file `oeplatform/securitysettings.py.default` and rename it `oeplatform/securitysettings.py`. Then, enter the connection to your above mentioned postgresql database.

### 3.1 Store and access database credentials

To setup the connection in the oeplatform project you can either setup environment variables that store the database connection credentials locally on your system or you can change the default value in the securitysetting.

!!! Note
    You have to provide the user name and password (with access to the oep_django and oedb database). Additionaly you can configure the databse name and the host and port variables if you dont run the database server using the default values.
#### 3.1.1 oep_django internal database

In the oeplatform/securitysettings.py file enter the database connection detials in this section:

!!! Info
    This code will attempt to collect the value from a environment variable in case it is not available the fallback value is used.

    `'NAME': os.environ.get("OEP_DJANGO_NAME", "oep_django")`

``` python
# oeplatform/securitysettings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get("OEP_DJANGO_NAME", "oep_django"),
	    'USER': os.environ.get("OEP_DJANGO_USER", "postgres"),
	    'PASSWORD': os.environ.get("OEP_DB_PW", "postgres"),
	    'HOST': os.environ.get("OEP_DJANGO_HOST", "localhost")
	}
}

```

!!! Using-environment-variables
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

        set OEP_DJANGO_USER=oep_django_user
        set OEP_DB_PW=<oep_django_password>

    In the following steps we'll provide the terminal commands but you always can set the environment variables via menus instead.

    - On linux

        export OEP_DJANGO_USER=oep_django_user
        export OEP_DB_PW=<oep_django_password>


#### 3.1.2 oedb primary database 

In the oeplatform/securitysettings.py file enter the database connection detials in this section:

``` python
# oeplatform/securitysettings.py

dbuser = os.environ.get("LOCAL_DB_USER", "postgres")
dbpasswd = os.environ.get("LOCAL_DB_PASSWORD", "postgres")
dbport = os.environ.get("LOCAL_DB_PORT", 5432)
dbhost = os.environ.get("LOCAL_DB_HOST", "localhost")
dbname = os.environ.get("LOCAL_DB_NAME", "oedb")
```

!!! Using-environment-variables

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

        set LOCAL_DB_USER=oep_db_user
        set LOCAL_DB_PASSWORD=<oep_db_password>
        set LOCAL_DB_NAME=oep_db

    - On linux

        export LOCAL_DB_USER=oep_db_user
        export LOCAL_DB_PASSWORD=<oep_db_password>
        export LOCAL_DB_NAME=oep_db

    !!! Tip
        If you kept the default name from the above example in 2.1, then the environment variables
        `LOCAL_DB_USER` and `LOCAL_DB_NAME` should have the values `oep_db_user` and `oep_db`, respectively.

## 4 Create the database tables

### 4.1 Django migrations

Finish the django database setup with this command

    python manage.py migrate
### 4.2 Alembic setup

In order to run the OEP website, the primary database needs some extra management tables.
We use `alembic` to keep track of changes in those tables. To create all tables that are needed, simply type

    python manage.py alembic upgrade head